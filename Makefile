install:
	pip install -r requirements.txt

run:
	python -m pipeline_template.pipeline

test:
	pytest

docker:
	docker build -t pipeline-template .
