.PHONY: test eval audit poc serve image eks-up eks-test eks-down
test:            ## unit + integration
	python3 -m pytest -q tests
eval:            ## golden-set gate (fails under threshold)
	python3 evals/run_golden.py
audit:           ## full prompts.chat audit -> promptvet-out/
	curl -sSL -o /tmp/prompts.csv https://raw.githubusercontent.com/f/prompts.chat/36c1131e85e4ff08ce4d908f0e907e3dbdd019a5/prompts.csv
	python3 -m promptvet scan /tmp/prompts.csv --out promptvet-out --skills 25 --source-name "prompts.chat (CC0)"
serve:
	OUT_DIR=public python3 scripts/build_report.py && python3 -m promptvet serve --port 8080
poc:             ## Vercel preview deploy (needs `vercel` CLI login) then e2e
	vercel deploy --yes > .vercel-url && BASE_URL=$$(cat .vercel-url) python3 -m pytest -q tests/e2e
image:
	docker build -t promptvet:dev .
eks-up:
	cd infra/eks/terraform && terraform init && terraform apply -auto-approve
eks-test:
	BASE_URL=$$(kubectl -n promptvet get ingress promptvet -o jsonpath='http://{.status.loadBalancer.ingress[0].hostname}') python3 -m pytest -q tests/e2e
eks-down:
	cd infra/eks/terraform && terraform destroy -auto-approve
