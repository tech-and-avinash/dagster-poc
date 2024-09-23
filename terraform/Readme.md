Steps to Apply:
For QA:
bash
```
cd environments/qa
terraform apply -var-file=qa.tfvars
```
For Prod:
bash
```
cd environments/prod
terraform apply -var-file=prod.tfvars
```