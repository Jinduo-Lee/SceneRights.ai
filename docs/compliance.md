# Compliance Specification (v6.2.2 Baseline)

## Permitted AI Baseline
- Runtime AI permitted exclusively: Google Gemini via Vertex AI (`google-genai`, `google-adk`).
- Prohibited in runtime: OpenAI, Anthropic, Claude, AWS AI, Microsoft AI, LangChain, CrewAI, AutoGen, external embedding/vision models.

## OpenCV Restriction
- Deterministic transforms only (e.g. HSV sampling, cropping).
- Strictly prohibited: `cv2.dnn`, `cv2.CascadeClassifier`, `cv2.face`, or any pretrained classifier.

