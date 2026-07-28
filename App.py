import streamlit as st
import pandas as pd
import numpy as np
import json

from pypdf import PdfReader

from sentence_transformers import SentenceTransformer

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)

model_name = "mistralai/Mistral-7B-Instruct-v0.3"

tokenizer = AutoTokenizer.from_pretrained(
    model_name
)

llm = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto"
)

def read_resume(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"

    return text


def extract_pdf(uploaded_file):
    return read_resume(uploaded_file)


def ask_llm(prompt):

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True
    ).to(llm.device)

    outputs = llm.generate(
        **inputs,
        max_new_tokens=2000,
        do_sample=False
    )

    answer = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    )

    return answer

def search_faiss(question,
                 embedding_model,
                 index,
                 chunks,
                 k=5):

    if embedding_model is None or index is None or not chunks:
        return []

    question_embedding = embedding_model.encode(
        [question],
        convert_to_numpy=True
    )

    distances, indices = index.search(
        question_embedding.astype("float32"),
        k
    )

    results = []

    for i in indices[0]:

        results.append(chunks[i])

    return results




st.title("🤖 AI Career Coach")


uploaded_file = st.file_uploader(
    "Upload your Resume PDF",
    type="pdf"
)


if uploaded_file:

    if st.button("Generate Roadmap"):

        resume_text = extract_pdf(uploaded_file)


        prompt = f"""
        Analyze this resume.

        Resume:
        {resume_text}

        Return JSON only:

        {{
        "skills":[],
        "experience":"",
        "education":"",
        "projects":[]
        }}
        """


        analysis = ask_llm(prompt)

        candidate = json.loads(analysis)


        st.subheader("Skills")

        for skill in candidate["skills"]:
            st.success(skill)


        query = " ".join(candidate["skills"])


        retrieved_documents = search_faiss(
            query,
            None,
            None,
            []
        )


        roadmap_prompt = f"""
        Create a career roadmap.

        Candidate:
        {candidate}

        Information:
        {retrieved_documents}

        Return JSON only.
        """


        roadmap = ask_llm(roadmap_prompt)

        roadmap = json.loads(roadmap)


        st.subheader("📚 Learning Roadmap")


        for item in roadmap["roadmap"]:

            st.write("### " + item["skill"])

            for resource in item["learning_resources"]:
                st.write("- " + resource)