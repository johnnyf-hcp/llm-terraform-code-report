def get():
    return [{'owner': 'jamiewri', 'name': 'snapshot-securing-access-to-kubernetes-with-boundary', 'full_name': 'jamiewri/snapshot-securing-access-to-kubernetes-with-boundary', 'files': [{'file_path': 'deploy/boundary-config/accounts.tf', 'content': '# Copyright (c) HashiCorp, Inc.\n# SPDX-License-Identifier: MPL-2.0\n\nresource "boundary_account_password" "user" {\n  for_each       = var.users\n  name           = lower(each.key)\n  description    = "Account password for ${each.key}"\n  auth_method_id = boundary_auth_method_password.password.id\n  login_name     = lower(each.key)\n  password       = "password123"\n}\n'}, {'file_path': 'deploy/boundary-config/admin.tf', 'content': 'resource "boundary_role" "org_admin_role" {\n  scope_id       = "global"\n  grant_scope_id = boundary_scope.global.id\n  grant_strings = [\n    "id=*;type=*;actions=*"\n  ]\n  principal_ids = [boundary_user.admin-user.id]\n}\n\nresource "boundary_auth_method_password" "admin-password" {\n  name        = "org_admin_password_auth"\n  description = "Password auth method for global org"\n  scope_id    = boundary_scope.global.id\n}\n\nresource "boundary_user" "admin-user" {\n  name        = "admin-user"\n  description = "User resource for admin-user"\n  account_ids = [boundary_account_password.admin-user.id]\n  scope_id    = boundary_scope.global.id\n}\n\nresource "boundary_account_password" "admin-user" {\n  name           = "admin-user"\n  description    = "Account password for admin-user"\n  auth_method_id = boundary_auth_method_password.admin-password.id\n  login_name     = "admin-user"\n  password       = "password123"\n}\n'}, {'file_path': 'deploy/boundary-config/auth_method.tf', 'content': '# Copyright (c) HashiCorp, Inc.\n# SPDX-License-Identifier: MPL-2.0\n\nresource "boundary_auth_method_password" "password" {\n  name        = "org_password_auth"\n  description = "Password auth method for org"\n  scope_id    = boundary_scope.org.id\n}\n'}, {'file_path': 'deploy/boundary-config/groups.tf', 'content': '# Copyright (c) HashiCorp, Inc.\n# SPDX-License-Identifier: MPL-2.0\n\nresource "random_shuffle" "group" {\n  input = [\n    for o in boundary_user.user : o.id\n  ]\n  result_count = floor(length(var.users) / 4)\n  count        = floor(length(var.users) / 2)\n}\n\nresource "random_pet" "group" {\n  length = 2\n  count  = length(var.users) / 2\n}\n\nresource "boundary_group" "group" {\n    for_each = {\n        for k, v in random_shuffle.group : k => v.id\n    }\n    name        = random_pet.group[each.key].id\n    description = "Group: ${random_pet.group[each.key].id}"\n    member_ids = tolist(random_shuffle.group[each.key].result)\n    scope_id = boundary_scope.org.id\n}\n'}, {'file_path': 'deploy/boundary-config/kube.tf', 'content': 'resource "boundary_credential_library_vault" "read-only" {\n  name                = "read-only"\n  description         = "Vault Dynamic Kubernetes Secerets Engine"\n  credential_store_id = boundary_credential_store_vault.vault-cred-store.id\n  path                = "kubernetes/creds/read-only"\n  http_method         = "POST"\n  http_request_body   = <<EOT\n{\n  "kubernetes_namespace": "app"\t\n}\nEOT\n}\n\nresource "boundary_credential_library_vault" "cicd-write" {\n  name                = "cicd-write"\n  description         = "Vault Dynamic Kubernetes Secerets Engine"\n  credential_store_id = boundary_credential_store_vault.vault-cred-store.id\n  path                = "kubernetes/creds/cicd-write"\n  http_method         = "POST"\n  http_request_body   = <<EOT\n{\n  "kubernetes_namespace": "app"\t\n}\nEOT\n}\n\nresource "boundary_credential_library_vault" "kubernetes-ca" {\n  name                = "kubernetes-ca"\n  description         = "Vault KV - Kubernetes CA"\n  credential_store_id = boundary_credential_store_vault.vault-cred-store.id\n  path                = "secret/data/k8s-cluster"\n  http_method         = "GET"\n}\n\nresource "boundary_host_catalog_static" "kubernetes" {\n  name        = "Kubernetes Clusters"\n  description = "Host Catalog contains all production Kubernetes clusters!"\n  scope_id    = boundary_scope.project.id\n}\n\nresource "boundary_host_static" "kubernetes" {\n  name            = "Kubernetes API"\n  description     = "Kubernetes API"\n  address         = "kubernetes.default.svc"\n  host_catalog_id = boundary_host_catalog_static.kubernetes.id\n}\n\nresource "boundary_host_set_static" "kubernetes" {\n  host_catalog_id = boundary_host_catalog_static.kubernetes.id\n  host_ids = [\n    boundary_host_static.kubernetes.id,\n  ]\n}\n\nresource "boundary_target" "kubernetes" {\n  name         = "Kubernetes Production"\n  description  = "Kubernetes Production Cluster"\n  type         = "tcp"\n  default_port = "443"\n  scope_id     = boundary_scope.project.id\n  host_source_ids = [\n    boundary_host_set_static.kubernetes.id\n  ]\n  brokered_credential_source_ids = [\n     boundary_credential_library_vault.cicd-write.id,\n     boundary_credential_library_vault.kubernetes-ca.id,\n  ]\n\n  egress_worker_filter = "\\"/tags/session_recording/0\\" == \\"true\\""\n  ingress_worker_filter = "\\"/tags/session_recording/0\\" == \\"true\\""\n}\n\nresource "vault_token" "boundary" {\n\n  policies = ["boundary-controller", "kv-read"]\n  renewable = true\n  no_parent = true\n  ttl = "48h"\n  renew_min_lease = 43200\n  renew_increment = 86400\n  no_default_policy = true\n  period = "2d"\n\n  metadata = {\n    "purpose" = "boundary-service-account"\n  }\n}\n\nresource "boundary_credential_store_vault" "vault-cred-store" {\n  name        = "HashiCorp Vault - Production"\n  description = "HashiCorp Vault in the Production VPC "\n  address     = "http://vault:8200"\n  token       = vault_token.boundary.client_token\n  scope_id    = boundary_scope.project.id\n  worker_filter = "\\"/tags/session_recording/0\\" == \\"true\\""\n}\n\n'}, {'file_path': 'deploy/boundary-config/outputs.tf', 'content': 'output "boundary_auth_method_password" {\n  value = boundary_auth_method_password.password.id\n}\n\noutput "boundary_auth_method_password_admin" {\n  value = boundary_auth_method_password.admin-password.id\n}\n\n'}, {'file_path': 'deploy/boundary-config/providers.tf', 'content': 'provider "boundary" {\n  addr = var.BOUNDARY_ADDR\n  recovery_kms_hcl = <<EOT\nkms "aead" {\n  purpose = "recovery"\n  aead_type = "aes-gcm"\n  key_id = "global_recovery"\n  key = "Ivj8Si8UQBp+Zm2lLbUDTxOGikE8rSo6QihCjWSTXqY="\n}\nEOT\n}\n\nvariable "BOUNDARY_ADDR" {}\n\nterraform {\n  required_providers {\n    boundary = {\n      source  = "hashicorp/boundary"\n      version = "1.1.8"\n    }\n    vault = {\n      source  = "hashicorp/vault"\n      version = "3.17.0"\n    }\n  }\n  backend "local" {}\n}\n\nvariable "VAULT_ADDR" {}\nprovider "vault" {\n  address = var.VAULT_ADDR\n}\n'}, {'file_path': 'deploy/boundary-config/roles.tf', 'content': '# Copyright (c) HashiCorp, Inc.\n# SPDX-License-Identifier: MPL-2.0\n\nresource "boundary_role" "global_anon_listing" {\n  scope_id = boundary_scope.global.id\n  grant_strings = [\n    "id=*;type=auth-method;actions=list,authenticate",\n    "id=*;type=scope;actions=*",\n    "id={{account.id}};actions=read,change-password",\n    "id=*;type=host-catalog;actions=*",\n    "type=host-catalog;actions=list"\n  ]\n  principal_ids = ["u_anon"]\n}\n\nresource "boundary_role" "org_anon_listing" {\n  scope_id = boundary_scope.org.id\n  grant_strings = [\n    "id=*;type=auth-method;actions=list,authenticate",\n    "id=*;type=scope;actions=*",\n    "id={{account.id}};actions=read,change-password",\n    "id=*;type=host-catalog;actions=*",\n    "type=host-catalog;actions=list"\n  ]\n  principal_ids = ["u_anon"]\n}\n\nresource "boundary_role" "org_admin" {\n  scope_id       = "global"\n  grant_scope_id = boundary_scope.org.id\n  grant_strings  = ["id=*;type=*;actions=*"]\n  principal_ids = concat(\n    [for user in boundary_user.user : user.id],\n    ["u_auth"]\n  )\n}\n\nresource "boundary_role" "proj_admin" {\n  scope_id       = boundary_scope.org.id\n  grant_scope_id = boundary_scope.project.id\n  grant_strings  = ["id=*;type=*;actions=*"]\n  principal_ids = concat(\n    [for user in boundary_user.user : user.id],\n    ["u_auth"],\n    [boundary_user.admin-user.id],\n  )\n}\n\nresource "boundary_role" "proj_anon_listing" {\n  scope_id       = boundary_scope.org.id\n  grant_scope_id = boundary_scope.project.id\n  grant_strings = [\n    "id=*;type=auth-method;actions=list,authenticate",\n    "id=*;type=scope;actions=*",\n    "id={{account.id}};actions=read,change-password",\n    "id=*;type=host-catalog;actions=*",\n    "type=host-catalog;actions=list"\n  ]\n  principal_ids = ["u_anon"]\n}\n'}, {'file_path': 'deploy/boundary-config/scopes.tf', 'content': '# Copyright (c) HashiCorp, Inc.\n# SPDX-License-Identifier: MPL-2.0\n\nresource "boundary_scope" "global" {\n  global_scope = true\n  name         = "global"\n  scope_id     = "global"\n}\n\nresource "boundary_scope" "org" {\n  scope_id    = boundary_scope.global.id\n  name        = "HashiBank"\n  description = "Primary organization scope"\n}\n\n\n\nresource "boundary_scope" "project" {\n  name                     = "Cloud-Ops"\n  description              = "Cloud-Ops Project"\n  scope_id                 = boundary_scope.org.id\n  auto_create_admin_role   = true\n  auto_create_default_role = true\n}\n\nresource "boundary_scope" "project-1" {\n  name                     = "IAM"\n  description              = "IAM Project"\n  scope_id                 = boundary_scope.org.id\n  auto_create_admin_role   = true\n  auto_create_default_role = true\n}\n\nresource "boundary_scope" "project-2" {\n  name                     = "Platform Engineering"\n  description              = "Platform Project"\n  scope_id                 = boundary_scope.org.id\n  auto_create_admin_role   = true\n  auto_create_default_role = true\n}\n'}, {'file_path': 'deploy/boundary-config/users.tf', 'content': '# Copyright (c) HashiCorp, Inc.\n# SPDX-License-Identifier: MPL-2.0\n\nresource "boundary_user" "user" {\n  for_each    = var.users\n  name        = each.key\n  description = "User resource for ${each.key}"\n  account_ids = [boundary_account_password.user[each.value].id]\n  scope_id    = boundary_scope.org.id\n}\n'}, {'file_path': 'deploy/boundary-config/vars.tf', 'content': '# Copyright (c) HashiCorp, Inc.\n# SPDX-License-Identifier: MPL-2.0\n\nvariable "addr" {\n  default = "http://127.0.0.1:9200"\n}\n\nvariable "users" {\n  type = set(string)\n  default = [\n    "jamie",\n    "jim",\n    "todd",\n    "randy",\n  ]\n}\n'}, {'file_path': 'deploy/vault-config/kv.tf', 'content': 'variable "ca_crt" {\n  type = string\n}\n\nresource "vault_kv_secret_v2" "kubernetes_ca" {\n  mount                      = "/secret"\n  name                       = "k8s-cluster"\n  cas                        = 1\n  delete_all_versions        = true\n  data_json                  = jsonencode(\n  {\n    ca_crt              = var.ca_crt\n  }\n  )\n}\n'}, {'file_path': 'deploy/vault-config/policy.tf', 'content': 'resource "vault_policy" "boundary-controller" {\n  name = "boundary-controller"\n\n  policy = <<EOT\npath "auth/token/lookup-self" {\n  capabilities = ["read"]\n}\n\npath "auth/token/renew-self" {\n  capabilities = ["update"]\n}\n\npath "auth/token/revoke-self" {\n  capabilities = ["update"]\n}\n\npath "sys/leases/renew" {\n  capabilities = ["update"]\n}\n\npath "sys/leases/revoke" {\n  capabilities = ["update"]\n}\n\npath "sys/capabilities-self" {\n  capabilities = ["update"]\n}\n# the next 2 were for testing\npath "ssh/issue/dymanic" {\n capabilities = ["create","update"]\n}\npath "*" {\n  capabilities = ["create", "read", "update", "delete", "list", "sudo"]\n}\n\nEOT\n}\n\nresource "vault_policy" "kv-read" {\n  name = "kv-read"\n\n  policy = <<EOT\npath "secret/data/my-secret" {\n  capabilities = ["read"]\n}\n\npath "secret/data/my-app-secret" {\n  capabilities = ["read"]\n}\nEOT\n}\n'}, {'file_path': 'deploy/vault-config/providers.tf', 'content': 'variable "VAULT_ADDR" {}\nprovider "vault" {\n  address = var.VAULT_ADDR\n}\n\nterraform {\n  required_providers {\n    vault = {\n      source  = "hashicorp/vault"\n      version = "3.17.0"\n    }\n  }\n  backend "local" {}\n}\n'}, {'file_path': 'deploy/vault-config/secret.kube.tf', 'content': 'resource "vault_kubernetes_secret_backend" "config" {\n  path                      = "kubernetes"\n  description               = "kubernetes secrets engine description"\n  default_lease_ttl_seconds = 43200\n  max_lease_ttl_seconds     = 86400\n  disable_local_ca_jwt      = false\n}\n\nresource "vault_kubernetes_secret_backend_role" "cicd-write" {\n  backend                       = vault_kubernetes_secret_backend.config.path\n  name                          = "cicd-write"\n  allowed_kubernetes_namespaces = ["*"]\n  token_max_ttl                 = 43200\n  token_default_ttl             = 600\n  kubernetes_role_type          = "Role"\n  generated_role_rules          = <<EOF\nrules:\n- apiGroups: [""]\n  resources: ["pods", "deployments", "services"]\n  verbs: ["get", "create", "update", "list", "delete"]\n- apiGroups: [""]\n  resources: ["events"]\n  verbs: ["get", "list"]\nEOF\n}\n\nresource "vault_kubernetes_secret_backend_role" "read-only" {\n  backend                       = vault_kubernetes_secret_backend.config.path\n  name                          = "read-only"\n  allowed_kubernetes_namespaces = ["*"]\n  token_max_ttl                 = 43200\n  token_default_ttl             = 600\n  kubernetes_role_type          = "Role"\n  generated_role_rules          = <<EOF\nrules:\n- apiGroups: [""]\n  resources: ["*"]\n  verbs: ["get", "list", "describe"]\n- apiGroups: ["rbac.authorization.k8s.io"]\n  resources: ["roles"]\n  verbs: ["get", "list", "describe"]\nEOF\n}\n\n'}]}]