# Firestore → Cloud Run Function (Client Provisioning)

This function listens to `clients/{clientId}` documents and automatically:

1. Creates a dedicated GCP project for the client under the `client-projects` folder (`CLIENT_FOLDER_ID`).
2. Links the billing account (optional) and enables the APIs required by the Meta Ads pipeline.
3. Creates the `meta_ads` BigQuery dataset inside the client's project.
4. Updates the `gs://clients-config/clients.json` manifest so the pipeline discovers the new client.

Everything runs on Cloud Functions (Gen 2), which internally executes on Cloud Run—no changes are needed in the Python `scripts/` directory.

---

## Event Payload

- Trigger: Firestore `google.cloud.firestore.document.v1.created`
- Resource: `projects/be-luma-infra/databases/(default)/documents/clients/{clientId}`
- Required Firestore fields:
  - `name`
  - `slug`
  - `business_id`
  - `project_id`
  - `google_ads_customer_id` (can be empty string)

---

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `CLIENT_FOLDER_ID` | `555317256759` | Folder where new projects are created |
| `CLIENTS_CONFIG_BUCKET` | `clients-config` | Bucket storing `clients.json` |
| `CLIENTS_CONFIG_FILENAME` | `clients.json` | Manifest file name |
| `DATASET_ID` | `meta_ads` | Dataset created inside each project |
| `BILLING_ACCOUNT_ID` | (empty) | Billing account to link (optional) |

---

## IAM / Service Account

Deploy the function with a service account that has, at minimum:

- `roles/resourcemanager.projectCreator`
- `roles/resourcemanager.folderViewer` (for the target folder)
- `roles/serviceusage.serviceUsageAdmin`
- `roles/serviceusage.apiKeysAdmin` (optional but useful)
- `roles/billing.projectManager` (if linking billing)
- `roles/storage.objectAdmin` on the `clients-config` bucket
- `roles/bigquery.admin` on the newly created projects (or grant at runtime via org policies)

Example service account: `project-creator@be-luma-infra.iam.gserviceaccount.com`

See `PERMISSIONS.md` for ready-to-run `gcloud`/`gsutil` commands that assign these roles.

---

## Deployment

See `DEPLOY.md` for an end-to-end `gcloud` command (Gen 2, Python 3.11). Update the env vars and service account before deploying.

