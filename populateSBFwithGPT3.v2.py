import numpy as np
import pandas as pd
from IPython import embed
import pandas as pd
import json, time
import argparse
from tqdm import tqdm
import openai
# openai.api_key = "sk-5sqlr5GGEcAf33RBvOnDFnzp547YNQPJHUNpSOYK" # UW key
# openai.api_key = "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" # Mosaic key
openai.api_key = "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" # CMU key

variables = [
  # 'conversationContext',
  'statement', 'speakerIdentity', 'listenerIdentity',
  # 'speakerListenerRelationship',
  'speechContext', 'intent', 
  'offensiveness', 'targetGroup', 'implication',
  'relevantPowerDynamics',
  'targetGroupReaction',
  'targetGroupEffect'
]
formatting = {
  'speakerIdentity': "[Speaker identity/characteristics] {}[/]",
  'listenerIdentity': "[Listener identity/characteristics] {}[/]",
  # 'speakerListenerRelationship': "Speaker-listener relationship: {}",
  'relevantPowerDynamics': "[Relevant power dynamics] {}[/]",
  'speechContext': "[Context of statement] {}[/]",
  'conversationContext': '[Conversational context] {}[/]',
  'statement': '[Statement] {}[/]',
  'intent': '[Intent] {}[/]',
  'offensiveness': '[Offensiveness] {}[/]',
  'targetGroup': '[Targeted/referenced minority group] {}[/]',
  'implication': '[Implied meaning/stereotype] {}[/]',
  'targetGroupReaction': '[Targeted minority group reaction] {}[/]'}
  'targetGroupEffect': '[Effect on targeted minority group] {}[/]'}
  
revFormat = {v.replace(" {}[/]",""): k for k,v in formatting.items()}
# formatting = {
#   'speakerIdentity': "Speaker identity/characteristics: {}",
#   'listenerIdentity': "Listener identity/characteristics: {}",
#   # 'speakerListenerRelationship': "Speaker-listener relationship: {}",
#   'relevantPowerDynamics': "Relevant power dynamics: {}",
#   'speechContext': "Context of statement: {}",
#   'conversationContext': 'Conversational context: {}',
#   'statement': 'Statement: {}',
#   'intent': 'Intent: {}',
#   'offensiveness': 'Offensiveness: {}',
#   'targetGroup': 'Targeted/referenced minority group: {}',
#   'implication': 'Implied meaning/stereotype: {}',
#   'targetGroupReaction': 'Targeted minority group reaction: {}'}

instructions = "Given a statement or a conversational snippet, explain the identities and power differentials of the speaker/listener, the intent behind the statement, why it might be offensive, and which minority group it targets."

def parseGPT3output(t):
  fields = [f.strip() for f in t.split("[/]") if f]
  out = {k: f.replace(p,"").strip() for p, k in revFormat.items() for f in fields if p in f}
  return out

def getGPT3prob(x,variant="text-davinci-001",attempt=0):
  time.sleep(0.06)
  try:
    r = openai.Completion.create(
      engine=variant,
      prompt=x,
      temperature=0.3,
      stop="\n\n",
      # n=3,
      # best_of=5,
      # top_p=0.5,
      max_tokens=160,
      logprobs=1,
    )
  except openai.error.APIError as e:
    print(e)
    print("Sleeping for 10 seconds")
    time.sleep(10)
    if attempt>10:
      print("Reached attempt limit, giving up")
      return None
    else:
      print("Trying again")
      return getGPT3prob(x,variant=variant,attempt=attempt+1)
    

  c = r["choices"][0]
  text = c["text"]
  logprobs = c["logprobs"]["token_logprobs"]
  # out = pd.Series(dict(socialContextGPT3=text,socialContextGPT3logprob=np.sum(logprobs)))
  totalEx = x.split("\n\n")[-1]+text
  d = parseGPT3output(totalEx)

  # d = {k: l.replace(v.replace(" {}",""),"").strip() for k, v in formatting.items() for l in totalEx.split("\n") if v.replace(" {}","") in l}
  d["logprob"] = np.sum(logprobs)

  return pd.Series(d)

def addExamplesToPost(p,examples,n=10):
  formattedExamples = "\n\n".join([
    "\n".join([formatting[v].format(e[v]) for v in variables if e[v] and not pd.isnull(e[v])])
    for ix, e in examples.sample(min(len(examples),n)).iterrows()
  ])
  return formattedExamples

def formatPosts(p,preamble="",**kwargs):
  # out = preamble+"\n\nStatement: "+p+"\nSocial context:"
  #f = [formatting[v].format(e[v]) for v in variables if e[v]]
  f = [formatting[v].format(p[kwargs[v+"_col"]])
       for v in variables if v+"_col" in kwargs and kwargs[v+"_col"] in p and p[kwargs[v+"_col"]] != ""]
  out = preamble+p["examples"]+"\n\n"+"\n".join(f)+"\n"
  out+= formatting[variables[variables.index("statement")+1]].split("{}")[0].strip()

  return out


def main(args):
  exampleFile = "promptExamples.v2.csv"
  examples = pd.read_csv(exampleFile)

  posts = pd.read_csv(args.input_file)
  if args.debug:
    posts = posts.sample(args.debug)

  posts = posts.rename(columns={"actual_quote": "post","text": "post"})
  posts["examples"] = posts[args.statement_col].apply(addExamplesToPost,examples=examples,n=args.n_examples)  
  fPosts = posts.apply(formatPosts,**args.__dict__,preamble=instructions,axis=1)
  tqdm.pandas(ascii=True)

          
  out = fPosts.progress_apply(getGPT3prob)
  cols = [c for c in variables if c in out.columns]
  out = out[cols]
  posts = pd.concat([posts,out],axis=1)

  try:
    del posts["post"]
  except:
    pass
  
  try:
    del posts["socialContextGPT3"]
    del posts["socialContextGPT3logprob"]
  except:
    pass
  
  posts.to_csv(args.output_file,index=False)
  

if __name__ =="__main__":
  p = argparse.ArgumentParser()
  p.add_argument("--input_file")
  p.add_argument("--statement_col",default="post")
  p.add_argument("--conversationContext_col",default="conversationContext")
  p.add_argument("--n_examples",default=7,type=int)
  p.add_argument("--debug",type=int,default=0)
  p.add_argument("--output_file")
  args = p.parse_args()
  main(args)


