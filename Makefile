REGIONS ?= ap-east-1 ap-northeast-1 ap-northeast-2 ap-south-1 ap-southeast-1 ap-southeast-2 ca-central-1 eu-central-1 eu-north-1 eu-west-1 eu-west-2 eu-west-3 me-south-1 sa-east-1 us-east-1 us-east-2 us-west-1 us-west-2
US_GOV_REGIONS ?= us-gov-west-1 us-gov-east-1
PYTHON_VERSIONS := 3.6 3.7 3.8
CERTBOT_ZIP_TARGETS := $(foreach ver,$(PYTHON_VERSIONS),certbot-layer-py$(ver).zip)
CERTBOT_TO_ACM_TARGET := certbot-to-acm.zip
DEPLOY_CERTBOT_LAYER_TARGETS := $(foreach region,$(REGIONS),deploy-certbot-layer-$(region))
DEPLOY_CERTBOT_LAYER_US_GOV_TARGETS := $(foreach region,$(US_GOV_REGIONS),deploy-certbot-layer-$(region))
DEPLOY_CERTBOT_TO_ACM_TARGETS := $(foreach region,$(REGIONS),deploy-certbot-to-acm-$(region))
DEPLOY_CERTBOT_TO_ACM_US_GOV_TARGETS := $(foreach region,$(US_GOV_REGIONS),deploy-certbot-to-acm-$(region))

all: $(CERTBOT_ZIP_TARGETS) $(CERTBOT_TO_ACM_TARGET)

certbot-layer-py%.zip: certbot-layer-py%.dockerfile createzip.py
	VER=$@
	docker build -t $(patsubst %.zip,%,$@) -f $< .
	mkdir -p ./export
	docker run --rm --mount type=bind,src=$(PWD)/export,target=/export $(patsubst %.zip,%,$@) cp /$@ /export
	mv ./export/$@ .

certbot-to-acm.zip: index.py
	rm -f certbot-to-acm.zip
	zip -9 certbot-to-acm.zip index.py

clean:
	rm certbot-layer-*.zip

.PHONY: all clean