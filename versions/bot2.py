import streamlit as st
import pandas as pd

df = pd.read_csv("troubleshooting.csv")

st.title("🛠 Troubleshooting Assistant")

equipments = df["Equipment"].unique()
selected_eq = st.selectbox("Select Equipment", equipments)

if selected_eq:
    errors = df[df["Equipment"] == selected_eq]["ERROR"].unique()
    selected_error = st.selectbox("Select Error Type", errors)

    if selected_error:
        desc = df[(df["Equipment"] == selected_eq) & 
                  (df["ERROR"] == selected_error)]["ERROR DESCRIPTION"].unique()
        selected_desc = st.selectbox("Select Error Description", desc)

        if selected_desc:
            steps = df[(df["Equipment"] == selected_eq) & 
                       (df["ERROR"] == selected_error) & 
                       (df["ERROR DESCRIPTION"] == selected_desc)]["ACTION POINTS / TROUBLE SHOOTING"].tolist()
            solution = df[(df["Equipment"] == selected_eq) & 
                          (df["ERROR"] == selected_error) & 
                          (df["ERROR DESCRIPTION"] == selected_desc)]["FINAL SOLUTIONS"].iloc[0]

            st.subheader("🔧 Troubleshooting Steps:")
            for step in steps:
                st.write(f"- {step}")

            if st.button("Did that fix the issue?"):
                st.success("Glad it worked!")
            else:
                st.warning(f" Final Solution: {solution}")
