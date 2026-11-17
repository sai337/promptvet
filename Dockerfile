# Build stage renders the audit report from a pinned prompts.chat snapshot.
FROM python:3.13-slim AS build
WORKDIR /src
COPY promptvet ./promptvet
COPY scripts ./scripts
COPY public ./public
ARG PROMPTS_CHAT_SHA=36c1131e85e4ff08ce4d908f0e907e3dbdd019a5
RUN PROMPTS_CHAT_SHA=$PROMPTS_CHAT_SHA python scripts/build_report.py

# Runtime: distroless, non-root, read-only, stdlib only.
FROM gcr.io/distroless/python3-debian12:nonroot
WORKDIR /app
COPY --from=build /src/promptvet ./promptvet
COPY --from=build /src/public ./public
ENV PYTHONDONTWRITEBYTECODE=1 PROMPTVET_STATIC=/app/public
EXPOSE 8080
USER nonroot
ENTRYPOINT ["python3", "-m", "promptvet", "serve", "--port", "8080"]
