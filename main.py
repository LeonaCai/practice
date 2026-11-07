from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path
import re
app=FastAPI(title="AI4KOnCo | Trustworthy AI Demonstrator",version="0.3-live",description="Synthetic-only, rule-based prototype. No clinical validation, LLM, RAG, or patient data.")
BASE=Path(__file__).parent

class ChatRequest(BaseModel):
    question:str=Field(min_length=2,max_length=1000)
    language:Literal["en","de"]="en"
    audience:Literal["child","parent"]="parent"
    age:int|None=Field(default=None,ge=0,le=120)
    level:Literal["simple","standard","detailed"]="simple"

NCI="https://www.cancer.gov/about-cancer/treatment/types/chemotherapy"
NCI_SIDE="https://www.cancer.gov/about-cancer/treatment/side-effects"
NCI_HELP="https://www.cancer.gov/about-cancer/coping/questions"
KB={
"chemotherapy":{"source":"National Cancer Institute (NCI)","url":NCI,"en":["Chemotherapy is medicine that helps fight cancer. Your care team can explain your treatment.","Chemotherapy uses medicines to destroy cancer cells or slow their growth. Different medicines can have different effects.","Chemotherapy targets processes involved in cancer-cell growth and survival. The choice of drugs, dosing, and monitoring depends on the diagnosis and oncology plan."],"de":["Chemotherapie ist eine Behandlung mit Medikamenten gegen Krebs. Das Behandlungsteam kann dir alles erklären.","Chemotherapie nutzt Medikamente, um Krebszellen zu bekämpfen oder ihr Wachstum zu verlangsamen.","Chemotherapeutika greifen Vorgänge an, die für das Wachstum und Überleben von Krebszellen wichtig sind. Die Auswahl ist individuell."]},
"side_effects":{"source":"National Cancer Institute (NCI)","url":NCI_SIDE,"en":["Some cancer medicines can make you tired or feel sick. Tell your care team how you feel.","Chemotherapy can cause side effects such as nausea, fatigue, or hair loss. They vary with the medicines and the person.","Side effects depend on the regimen and patient factors. The oncology team can explain expected effects, monitoring, and how to respond to new symptoms."],"de":["Manche Krebsmedikamente können müde machen oder Übelkeit verursachen. Sprich mit deinem Behandlungsteam.","Eine Chemotherapie kann unter anderem Müdigkeit, Übelkeit oder Haarausfall verursachen. Die Wirkungen sind unterschiedlich.","Nebenwirkungen hängen unter anderem von den eingesetzten Medikamenten ab. Bitte klären Sie Risiken und Symptome mit dem Behandlungsteam."]},
"doctor_questions":{"source":"National Cancer Institute (NCI)","url":NCI_HELP,"en":["You can ask your doctor what will happen next and who can help if you feel worried.","You might ask what the treatment aims to do, which side effects to watch for, and whom to contact after hours.","Prepare questions about treatment goals, alternatives, side effects, monitoring, and when you should contact the oncology team."],"de":["Du darfst fragen, was als Nächstes passiert und wen du fragen kannst, wenn du Angst hast.","Fragen Sie nach dem Ziel der Behandlung, möglichen Nebenwirkungen und Kontaktpersonen.","Bereiten Sie Fragen zu Behandlungszielen, Alternativen, Nebenwirkungen, Verlaufskontrollen und Kontaktwegen vor."]}
}
UR={"en":"I cannot assess urgent symptoms. If a child receiving cancer treatment develops a fever, breathing difficulties, severe bleeding, seizures or another concerning symptom, contact the treating oncology team immediately according to its instructions. In immediate danger, call emergency services. Do not rely on this demo for triage.","de":"Diese Demo kann keine akuten Beschwerden beurteilen. Bitte wenden Sie sich bei Fieber, Atemnot, starken Blutungen, Krampfanfällen oder anderen besorgniserregenden Symptomen während einer Krebsbehandlung sofort nach den Anweisungen an das Behandlungsteam. Bei akuter Gefahr rufen Sie den Notruf."}
CL={"en":"Could you explain whether you mean a medical term, a treatment question, or a new symptom? If the child is unwell during cancer treatment, contact the treating team rather than waiting for this demo.","de":"Meinen Sie einen medizinischen Begriff, eine Frage zur Behandlung oder ein neues Symptom? Bei Beschwerden während einer Krebsbehandlung wenden Sie sich bitte an das Behandlungsteam."}
PERSONAL={"en":"Only your child's oncology team can recommend an individual treatment using confirmed clinical information. This demo cannot make that decision. Ask: Which treatment options are appropriate for my child, and why?","de":"Nur das behandelnde onkologische Team kann anhand gesicherter Befunde eine individuelle Behandlung empfehlen. Diese Demo kann das nicht. Fragen Sie: Welche Optionen kommen für mein Kind infrage und warum?"}
UNKNOWN={"en":"I do not have a prepared answer to that question. Please ask about chemotherapy, side effects, or questions for the medical team. For individual care, contact your child's clinicians.","de":"Dazu habe ich keine vorbereitete Antwort. Fragen Sie nach Chemotherapie, Nebenwirkungen oder Fragen an das Behandlungsteam. Für individuelle Anliegen wenden Sie sich an die Klinik."}
DISCLAIMER={"en":"Educational demonstration only; examples have not been clinically reviewed or tailored to a patient.","de":"Nur eine Demonstration; nicht klinisch geprüft und nicht auf einzelne Patienten abgestimmt."}
SCENARIOS=[
("General medical information","What is chemotherapy?","chemotherapy"),
("Side effects","What are the side effects of chemotherapy?","side_effects"),
("Clarifying question","My child is sick.","clarify"),
("Clinical decision boundary","Which treatment is best for my child?","individual_treatment"),
("Potentially urgent concern","My child has a fever during chemotherapy.","urgent_caution"),
("Unsupported question","Can you interpret my blood test results?","unknown")
]
INSIGHTS=[
{"id":"child_fatigue","role":"child","label":"Child's private concern","text":"I feel tired every evening, but I'm afraid to tell anyone.","observations":[{"label":"Self-reported experience","value":"tiredness"},{"label":"Time expression","value":"every evening"},{"label":"Disclosure preference","value":"hesitant to disclose"}],"next_step":"Suggest a trusted clinician or adult and follow agreed safeguarding and permission rules.","boundary":"No automatic disclosure, diagnosis, or risk score."},
{"id":"daily_checkin","role":"child","label":"Daily routine pattern","text":"Day 1: tired in evening. Day 2: tired in evening. Day 3: slept poorly.","observations":[{"label":"Reported theme","value":"fatigue and sleep"},{"label":"Repeated mention","value":"evening fatigue × 2"},{"label":"Data type","value":"three fictional check-ins"}],"next_step":"Show symptom trends to an authorized clinician for review.","boundary":"Do not infer cancer stage or treatment response."},
{"id":"caregiver_nutrition","role":"caregiver","label":"Caregiver research theme","text":"My child struggles to eat after treatment. We need help with appetite.","observations":[{"label":"Candidate topic","value":"nutrition and appetite"},{"label":"Context","value":"post-treatment caregiving"},{"label":"Research output","value":"topic label for expert review"}],"next_step":"With separate research consent, study appropriately protected aggregated themes.","boundary":"No automated care protocol and no cross-family data disclosure."}
]
def response(p:ChatRequest):
    q=re.sub(r"\s+"," ",p.question.strip().casefold())
    lang=p.language
    level=p.level
    if p.audience=="child" and (p.age is None or p.age<12):level="simple"
    elif p.audience=="child" and level=="detailed":level="standard"
    i={"simple":0,"standard":1,"detailed":2}[level]
    intent="unknown";type="safe_fallback";policy="No grounded response -> abstain";matched=False;clinician=True;answer=UNKNOWN[lang];src=None;url=None
    if re.search(r"\b(fever|high temperature|difficulty breathing|trouble breathing|seizure|heavy bleeding|fieber|atemnot|krampfanfall|starke blutung)\b",q):
        intent="urgent_caution";type="safety_escalation";policy="Urgent keyword caution";answer=UR[lang]
    elif re.search(r"(which|what) (treatment|medicine|drug) (is|would be) best|welche behandlung|was soll mein kind nehmen",q):
        intent="individual_treatment";type="clinical_boundary";policy="No personal treatment recommendation";answer=PERSONAL[lang]
    elif re.fullmatch(r"(my child is sick|my kid is sick|my child feels bad|mein kind ist krank|meinem kind geht es schlecht)[.!? ]*",q):
        intent="clarify";type="clarifying_question";policy="Ambiguous input: clarify";answer=CL[lang]
    else:
        if re.search(r"side effect|nausea|hair loss|nebenwirkung|übelkeit|haarausfall",q):intent="side_effects"
        elif re.search(r"ask.*doctor|questions.*doctor|ask.*physician|fragen.*arzt|ärzt",q):intent="doctor_questions"
        elif re.search(r"chemo|chemotherapie",q):intent="chemotherapy"
        if intent in KB:
            item=KB[intent];answer=item[lang][i];src=item["source"];url=item["url"];type="educational";policy="Prewritten general information";matched=True;clinician=False
        else:intent="unknown"
    return {"intent":intent,"answer":answer,"source_title":src,"source_url":url,"review_status":"demo_not_clinically_reviewed","needs_clinician":clinician,"matched":matched,"disclaimer":DISCLAIMER[lang],"response_type":type,"applied_level":level,"audience":p.audience,"language":lang,"policy":policy,"suggested_questions":[],"pipeline":[{"stage":"Input","detail":p.audience+" | "+lang+" | "+level},{"stage":"Safety","detail":policy},{"stage":"Routing","detail":intent},{"stage":"Evidence","detail":"Reference link, not clinical approval" if src else "No source attached"}]}

@app.get("/",include_in_schema=False)
@app.get("/app",include_in_schema=False)
async def index():
    return HTMLResponse((BASE/"index.html").read_text(encoding="utf-8"))
@app.get("/health")
def health():return {"status":"ok","mode":"deterministic_rule_based","clinical_review":"not_completed","api_version":"0.3-live"}
@app.get("/capabilities")
def capabilities():return {"uses_llm":False,"uses_rag":False,"persistent_chat_memory":False,"medical_review":"not_completed","patient_data_connected":False,"knowledge_topics":len(KB),"languages":["en","de"],"chat_endpoint":"/chat","synthetic_insights_only":True}
@app.get("/knowledge")
def knowledge():return {"review_status":"demo_not_clinically_reviewed","topics":[{"id":k,"title":k.replace("_"," ").title(),"source_title":v["source"],"source_url":v["url"]} for k,v in KB.items()]}
@app.get("/scenarios")
def scenarios():return {"scenarios":[{"id":str(i),"title":t,"question":q,"expected_intent":expected} for i,(t,q,expected) in enumerate(SCENARIOS)]}
@app.post("/chat")
def chat(p:ChatRequest):return response(p)
@app.get("/insights/samples")
def samples():return {"synthetic":True,"samples":[{"id":s["id"],"label":s["label"],"role":s["role"],"text":s["text"]} for s in INSIGHTS]}
@app.get("/insights/demo/{sample_id}")
def sample(sample_id:str):
    for s in INSIGHTS:
        if s["id"]==sample_id:return {"synthetic":True,"clinically_validated":False,"mode":"predefined_fixture",**s}
    raise HTTPException(status_code=404,detail="Unknown synthetic scenario")
