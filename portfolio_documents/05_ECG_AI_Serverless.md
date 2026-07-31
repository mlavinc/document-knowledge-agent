# 05 — Project: ECG AI Serverless

## Overview

**ECG AI Serverless** (also Electrocardiogram AI Serverless / ECG-AI Serverless) is a portfolio project by Martín Lavín (Martin Lavin). It classifies short ECG fragments into arrhythmia-related rhythm classes using machine learning, deployed as a fully serverless AWS backend.

Repository: github.com/mlavinc/ecg-ai-serverless

## What it does

- Detects and classifies ECG fragments into six arrhythmia-related classes.
- Uses a **Random Forest** model trained on statistical, HRV, and frequency-domain features.
- Runs inference inside **AWS Lambda** with the model cached from **S3**.
- Frontend hosted on Vercel (React / Vite); backend can be created/destroyed with Terraform for demos.

## Dataset context

PhysioNet ECG Fragment Database for Dangerous Arrhythmia (2022), about **1016** fragments across six classes (including Dangerous_VFL_VF, Special_Form_VTTdP, Threatening_VT, Potential_Dangerous, Supraventricular, Sinus_rhythm).

## Technology stack

Python, Scikit-learn, NumPy, AWS Lambda, Amazon S3, API Gateway / Lambda Function URL patterns, Terraform, React frontend.

## Natural-language Q&A

**Tell me about ECG AI Serverless / Explain the ECG project.**
Martín built a serverless ECG arrhythmia classifier: feature-based Random Forest inference on AWS Lambda, model artifacts in S3, and a React UI for demos — combining ML and cloud infrastructure.

**What did Martin build with machine learning?**
ECG AI Serverless is his main ML cloud project: arrhythmia classification packaged as scalable serverless inference.
