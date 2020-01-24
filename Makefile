REGIONS ?= ap-east-1 ap-northeast-1 ap-northeast-2 ap-south-1 ap-southeast-1 ap-southeast-2 ca-central-1 eu-central-1 eu-north-1 eu-west-1 eu-west-2 eu-west-3 me-south-1 sa-east-1 us-east-1 us-east-2 us-west-1 us-west-2
PYTHON_VERSIONS := 3.6 3.7 3.8
CERTBOT_ZIP_TARGETS := $(foreach ver,$(PYTHON_VERSIONS),certbot-layer-py$(ver).zip)
DEPLOY_TARGETS := $(foreach region,$(REGIONS),deploy-$(REGION))

all: $(CERTBOT_ZIP_TARGETS)

certbot-layer-py%.zip: certbot-layer-%.dockerfile createzip.py
	VER=$@
	docker build -t $(patsubst %.zip,%,$@) -f $< .
	mkdir -p ./export
	docker run --rm --mount type=bind,src=$(PWD)/export,target=/export $(patsubst %.zip,%,$@) cp /$@ /export
	mv ./export/$@ .

clean:
	rm certbot-layer-*.zip

deploy: $(patsubst %,deploy-%,$(REGIONS))

deploy-%: $(CERTBOT_ZIP_TARGETS)
	./deploy.py --region $(patsubst deploy-%,%,$@) $(PYTHON_VERSIONS)

.PHONY: all clean deploy $(DEPLOY_TARGETS)
