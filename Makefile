REGIONS := us-west-2
PYTHON_VERSIONS := 3.6 3.7 3.8
CERTBOT_ZIP_TARGETS := $(foreach ver,$(PYTHON_VERSIONS),certbot-layer-$(ver).zip)
DEPLOY_TARGETS := $(foreach region,$(REGIONS),deploy-$(REGION))

all: $(CERTBOT_ZIP_TARGETS)

certbot-layer-%.zip: certbot-layer-%.dockerfile getbaseline.py zipdiffs.py
	VER=$@
	docker build -t $(patsubst %.zip,%,$@) -f $< .
	mkdir -p ./export
	docker run --rm --mount type=bind,src=$(PWD)/export,target=/export $(patsubst %.zip,%,$@) cp /$@ /export
	mv ./export/$@ .

clean:
	rm certbot-layer-*.zip

deploy: $(patsubst %,deploy-%,$(REGIONS))

deploy-%: $(CERTBOT_ZIP_TARGETS)
	for ver in $(PYTHON_VERSIONS); do \
		aws --region $(patsubst deploy-%,%,$@) lambda publish-layer-version \
			--layer-name certbottest --description "Certbot for Python $$ver" \
			--compatible-runtimes python$$ver --license-info Apache-2.0 \
			--zip-file fileb://certbot-layer-$$ver.zip; \
	done

.PHONY: all clean deploy $(DEPLOY_TARGETS)
