#!/usr/bin/env bash
# Independent disk-only verification of generate-security-skill-files output.
# Counts only; never reads a SKILL.md body except for the exact char-count and
# the targeted greps the contract requires.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

EXPECTED_SKILL_FILES=276
EXPECTED_FILE_TRACKED=276
FAIL=""

chk() { # name actual expected
  if [ "$2" != "$3" ]; then FAIL="$FAIL\n  - $1: got $2, expected $3"; fi
}

chk "skills/**/SKILL.md count" "$(find skills -name SKILL.md | wc -l | tr -d ' ')" "$EXPECTED_SKILL_FILES"
chk "AGENTS.md ledger rows" "$(grep -cE '^\| [A-Z]*T[0-9]' AGENTS.md | tr -d ' ')" "$EXPECTED_SKILL_FILES"
chk "unique CM IDs on disk" "$(find skills -name SKILL.md -path '*/*T[0-9]*-*/*' | sed -E 's|.*/([A-Z]*T[0-9]+)-.*|\1|' | sort -u | wc -l | tr -d ' ')" "$EXPECTED_FILE_TRACKED"
chk "library-lookup artifacts" "$(ls .sde-security/library-lookup/*.json | wc -l | tr -d ' ')" "$EXPECTED_FILE_TRACKED"
chk "cm-work content offloads" "$(ls .sde-security/cm-work/*.json | wc -l | tr -d ' ')" "$EXPECTED_SKILL_FILES"
chk "handoff library_lookup_audit" "$(python3 -c "import json;print(len(json.load(open('.sde-handoff.json'))['library_lookup_audit']))")" "$EXPECTED_FILE_TRACKED"
chk "handoff skill_files" "$(python3 -c "import json;print(len(json.load(open('.sde-handoff.json'))['skill_files']))")" "$EXPECTED_SKILL_FILES"

# --- every selected file-tracked CM has a project-requirements artifact ---
missing_req=0
for cm in CT9 T101 T105 T106 T114 T1144 T1145 T1150 T1151 T1154 T1155 T1156 T1157 T1158 T1159 T116 T1166 T1167 T1172 T1173 T1174 T1175 T1176 T1177 T1186 T1187 T1188 T1189 T119 T1190 T1191 T1192 T1193 T1194 T1195 T1196 T1197 T1198 T1199 T1200 T1201 T1202 T1203 T1204 T1205 T1206 T1207 T1208 T1209 T1210 T1211 T1212 T1213 T1214 T1215 T122 T1234 T1235 T1236 T1237 T128 T1362 T1363 T1365 T1392 T1468 T15 T151 T1539 T1540 T1541 T1542 T156 T166 T167 T17 T175 T18 T184 T186 T1887 T1889 T1917 T1918 T1919 T1922 T197 T20 T21 T2105 T2106 T2109 T2110 T2115 T2116 T2139 T214 T2140 T2141 T2142 T2256 T2257 T2258 T226 T2276 T2277 T228 T2282 T230 T2349 T2357 T241 T2485 T2486 T257 T2596 T2597 T2598 T2599 T2600 T2601 T2602 T2603 T2605 T2606 T2607 T2608 T2609 T2610 T2611 T2612 T2614 T2615 T2616 T2619 T2620 T2621 T2652 T2661 T2662 T2663 T2665 T2666 T279 T281 T284 T29 T295 T296 T305 T318 T32 T323 T338 T340 T349 T35 T350 T36 T373 T374 T378 T38 T3903 T3905 T3906 T3907 T3908 T3913 T3915 T3916 T3920 T3922 T3923 T3924 T3925 T3930 T3932 T3933 T394 T395 T406 T407 T42 T43 T439 T4433 T4434 T4435 T4436 T4437 T4438 T4439 T4440 T4441 T4442 T4443 T4444 T4445 T4446 T4447 T4448 T4449 T445 T4450 T4451 T4452 T4453 T4454 T446 T4601 T4746 T4747 T4748 T4749 T4750 T4751 T49 T50 T536 T537 T558 T573 T576 T587 T589 T59 T60 T61 T659 T66 T69 T70 T7353 T7354 T7355 T7356 T7357 T7358 T7359 T7360 T7361 T7362 T7363 T7364 T7365 T7366 T7367 T7368 T7369 T7370 T7371 T7372 T7373 T7374 T7375 T7376 T7377 T7378 T7379 T7380 T7381 T7382 T7411 T7412 T7414 T7415 T75 T76 T78 T85 T86 T87 T89 T96 T98; do
  [ -f ".sde-security/project-requirements/$cm.json" ] || missing_req=$((missing_req+1))
done
chk "project-requirements artifacts missing" "$missing_req" "0"

# --- per library file: char count == amendment length + appended length ---
bad_len=0
while IFS='|' read -r path src app; do
  [ -n "$path" ] || continue
  actual=$(python3 -c "import sys;print(len(open(sys.argv[1],encoding='utf-8',newline='').read()))" "$path")
  want=$((src + app))
  if [ "$actual" != "$want" ]; then
    bad_len=$((bad_len+1))
    FAIL="$FAIL\n  - fidelity $path: $actual chars, expected $want"
  fi
done <<'LIBLEN'
skills/input-validation/T1144-python/SKILL.md|5058|0
skills/container-security/T1150-docker/SKILL.md|4829|0
skills/container-security/T1151-docker/SKILL.md|4966|0
skills/container-security/T1154-docker/SKILL.md|4385|0
skills/container-security/T1156-docker/SKILL.md|4454|0
skills/container-security/T1158-docker/SKILL.md|4925|0
skills/cryptography/T1166-docker/SKILL.md|4925|0
skills/container-security/T1174-docker/SKILL.md|3021|0
skills/container-security/T1176-docker/SKILL.md|3318|0
skills/container-security/T1177-docker/SKILL.md|4563|0
skills/secrets-management/T1186-docker/SKILL.md|3601|0
skills/secrets-management/T1187-docker/SKILL.md|4202|0
skills/container-security/T1188-docker/SKILL.md|4321|0
skills/container-security/T1189-docker/SKILL.md|4172|0
skills/container-security/T1190-docker/SKILL.md|4632|0
skills/container-security/T1191-docker/SKILL.md|4562|0
skills/container-security/T1192-docker/SKILL.md|3742|0
skills/container-security/T1194-docker/SKILL.md|3098|0
skills/container-security/T1196-docker/SKILL.md|3221|0
skills/container-security/T1198-docker/SKILL.md|2999|0
skills/container-security/T1200-docker/SKILL.md|2518|0
skills/container-security/T1202-docker/SKILL.md|2817|0
skills/container-security/T1204-docker/SKILL.md|3130|0
skills/container-security/T1206-docker/SKILL.md|3008|0
skills/container-security/T1208-docker/SKILL.md|2736|0
skills/container-security/T1210-docker/SKILL.md|2930|0
skills/container-security/T1212-docker/SKILL.md|2986|0
skills/container-security/T1214-docker/SKILL.md|3176|0
skills/api-security/T1362-python/SKILL.md|3910|3593
skills/input-validation/T1365-python/SKILL.md|4655|0
skills/cryptography/T151-python/SKILL.md|5044|908
skills/api-security/T1541-python/SKILL.md|3370|0
skills/api-security/T1542-python/SKILL.md|3457|0
skills/api-security/T166-python/SKILL.md|4842|0
skills/authorization/T17-python/SKILL.md|3557|0
skills/authorization/T184-python/SKILL.md|3488|0
skills/dependency-management/T186-python/SKILL.md|3875|0
skills/authentication/T1887-python/SKILL.md|3642|10245
skills/authorization/T18-python/SKILL.md|3593|0
skills/authentication/T1919-python/SKILL.md|3497|0
skills/authentication/T1922-python/SKILL.md|3697|10362
skills/authentication/T20-python/SKILL.md|3596|359
skills/api-security/T2139-python/SKILL.md|4049|0
skills/authorization/T2141-python/SKILL.md|4407|0
skills/authorization/T2142-python/SKILL.md|3749|0
skills/cryptography/T21-python/SKILL.md|4390|3922
skills/api-security/T257-python/SKILL.md|3896|0
skills/authorization/T2598-python/SKILL.md|3234|0
skills/api-security/T2609-python/SKILL.md|4480|0
skills/cryptography/T295-python/SKILL.md|3437|403
skills/api-security/T29-python/SKILL.md|4283|0
skills/input-validation/T32-python/SKILL.md|3298|1084
skills/authentication/T338-python/SKILL.md|3664|2036
skills/input-validation/T36-python/SKILL.md|5172|0
skills/input-validation/T38-python/SKILL.md|4616|0
skills/authentication/T394-python/SKILL.md|3177|0
skills/input-validation/T42-python/SKILL.md|3165|0
skills/input-validation/T43-python/SKILL.md|3359|0
skills/input-validation/T4434-python/SKILL.md|5033|0
skills/input-validation/T4435-python/SKILL.md|4576|0
skills/input-validation/T4438-python/SKILL.md|5934|0
skills/input-validation/T4445-python/SKILL.md|4373|0
skills/input-validation/T4446-python/SKILL.md|4963|0
skills/infrastructure-hardening/T49-python/SKILL.md|5449|1024
skills/authorization/T50-python/SKILL.md|3509|0
skills/cryptography/T59-python/SKILL.md|3618|0
skills/cryptography/T60-python/SKILL.md|3702|0
skills/authentication/T69-python/SKILL.md|3834|0
skills/authentication/T70-python/SKILL.md|3758|0
skills/api-security/T75-python/SKILL.md|3343|0
skills/secrets-management/T76-python/SKILL.md|3112|0
LIBLEN
chk "library files with wrong length" "$bad_len" "0"

# --- appended section must not contain template anchors or amendment headings ---
bad_anchor=0
for f in "$@"; do :; done
while read -r f; do
  [ -n "$f" ] || continue
  sec=$(awk '/^## Additional Requirements \(SD Elements project\)$/{flag=1} flag' "$f")
  if [ -n "$sec" ]; then
    printf '%s' "$sec" | grep -qE '\*\*(Status|Category|Spec Context):\*\*' && { bad_anchor=$((bad_anchor+1)); FAIL="$FAIL\n  - template anchor in appended section: $f"; }
    printf '%s' "$sec" | grep -qE '^### [A-Z]*T[0-9]+ - SKILL\.md - ' && { bad_anchor=$((bad_anchor+1)); FAIL="$FAIL\n  - amendment heading in appended section: $f"; }
  fi
done <<'LIBFILES'
skills/input-validation/T1144-python/SKILL.md
skills/container-security/T1150-docker/SKILL.md
skills/container-security/T1151-docker/SKILL.md
skills/container-security/T1154-docker/SKILL.md
skills/container-security/T1156-docker/SKILL.md
skills/container-security/T1158-docker/SKILL.md
skills/cryptography/T1166-docker/SKILL.md
skills/container-security/T1174-docker/SKILL.md
skills/container-security/T1176-docker/SKILL.md
skills/container-security/T1177-docker/SKILL.md
skills/secrets-management/T1186-docker/SKILL.md
skills/secrets-management/T1187-docker/SKILL.md
skills/container-security/T1188-docker/SKILL.md
skills/container-security/T1189-docker/SKILL.md
skills/container-security/T1190-docker/SKILL.md
skills/container-security/T1191-docker/SKILL.md
skills/container-security/T1192-docker/SKILL.md
skills/container-security/T1194-docker/SKILL.md
skills/container-security/T1196-docker/SKILL.md
skills/container-security/T1198-docker/SKILL.md
skills/container-security/T1200-docker/SKILL.md
skills/container-security/T1202-docker/SKILL.md
skills/container-security/T1204-docker/SKILL.md
skills/container-security/T1206-docker/SKILL.md
skills/container-security/T1208-docker/SKILL.md
skills/container-security/T1210-docker/SKILL.md
skills/container-security/T1212-docker/SKILL.md
skills/container-security/T1214-docker/SKILL.md
skills/api-security/T1362-python/SKILL.md
skills/input-validation/T1365-python/SKILL.md
skills/cryptography/T151-python/SKILL.md
skills/api-security/T1541-python/SKILL.md
skills/api-security/T1542-python/SKILL.md
skills/api-security/T166-python/SKILL.md
skills/authorization/T17-python/SKILL.md
skills/authorization/T18-python/SKILL.md
skills/authorization/T184-python/SKILL.md
skills/dependency-management/T186-python/SKILL.md
skills/authentication/T1887-python/SKILL.md
skills/authentication/T1919-python/SKILL.md
skills/authentication/T1922-python/SKILL.md
skills/authentication/T20-python/SKILL.md
skills/cryptography/T21-python/SKILL.md
skills/api-security/T2139-python/SKILL.md
skills/authorization/T2141-python/SKILL.md
skills/authorization/T2142-python/SKILL.md
skills/api-security/T257-python/SKILL.md
skills/authorization/T2598-python/SKILL.md
skills/api-security/T2609-python/SKILL.md
skills/api-security/T29-python/SKILL.md
skills/cryptography/T295-python/SKILL.md
skills/input-validation/T32-python/SKILL.md
skills/authentication/T338-python/SKILL.md
skills/input-validation/T36-python/SKILL.md
skills/input-validation/T38-python/SKILL.md
skills/authentication/T394-python/SKILL.md
skills/input-validation/T42-python/SKILL.md
skills/input-validation/T43-python/SKILL.md
skills/input-validation/T4434-python/SKILL.md
skills/input-validation/T4435-python/SKILL.md
skills/input-validation/T4438-python/SKILL.md
skills/input-validation/T4445-python/SKILL.md
skills/input-validation/T4446-python/SKILL.md
skills/infrastructure-hardening/T49-python/SKILL.md
skills/authorization/T50-python/SKILL.md
skills/cryptography/T59-python/SKILL.md
skills/cryptography/T60-python/SKILL.md
skills/authentication/T69-python/SKILL.md
skills/authentication/T70-python/SKILL.md
skills/api-security/T75-python/SKILL.md
skills/secrets-management/T76-python/SKILL.md
LIBFILES
chk "library appended-section violations" "$bad_anchor" "0"

# --- template files must carry no Additional Requirements section, no placeholders ---
bad_tmpl=0
while read -r f; do
  [ -n "$f" ] || continue
  grep -qF '## Additional Requirements (SD Elements project)' "$f" && { bad_tmpl=$((bad_tmpl+1)); FAIL="$FAIL\n  - template carries Additional Requirements: $f"; }
  grep -qE '\{ID\}|\{Title\}|\{file_path\}|\{current_code\}|\{secure_code_pattern\}|\{who/what|TODO:' "$f" && { bad_tmpl=$((bad_tmpl+1)); FAIL="$FAIL\n  - unfilled placeholder: $f"; }
done <<'TMPLFILES'
skills/infrastructure-hardening/CT9-ismenia/SKILL.md
skills/input-validation/T101-test-that-application-is-not-vulnerable-to-sql-i/SKILL.md
skills/infrastructure-hardening/T105-verify-that-your-application-does-not-have-unnec/SKILL.md
skills/authorization/T106-test-that-site-is-not-vulnerable-to-direct-objec/SKILL.md
skills/authentication/T114-test-system-to-system-authentication-lockout-or/SKILL.md
skills/input-validation/T1145-verify-if-web-page-template-is-vulnerable-to-sst/SKILL.md
skills/container-security/T1155-verify-that-docker-registries-are-secure-docker/SKILL.md
skills/container-security/T1157-verify-that-the-aufs-storage-driver-is-not-used/SKILL.md
skills/container-security/T1159-verify-that-tls-authentication-is-configured-for/SKILL.md
skills/api-security/T116-test-for-regular-expression-denial-of-service/SKILL.md
skills/cryptography/T1167-verify-that-data-exchanged-between-containers-on/SKILL.md
skills/container-security/T1172-secure-daemon-configuration-files-docker/SKILL.md
skills/container-security/T1173-verify-that-daemon-configuration-files-are-secur/SKILL.md
skills/container-security/T1175-verify-that-containers-are-not-run-as-root-docke/SKILL.md
skills/api-security/T119-test-for-clickjacking/SKILL.md
skills/container-security/T1193-test-if-unnecessary-host-resources-are-exposed-d/SKILL.md
skills/container-security/T1195-test-if-ssh-is-running-within-containers-docker/SKILL.md
skills/container-security/T1197-test-if-only-needed-ports-are-open-on-the-contai/SKILL.md
skills/container-security/T1199-test-that-the-host-s-network-namespace-is-not-sh/SKILL.md
skills/container-security/T1201-test-that-resources-used-by-containers-are-limit/SKILL.md
skills/container-security/T1203-test-if-container-cpu-priority-is-appropriately/SKILL.md
skills/container-security/T1205-test-if-the-container-s-root-file-system-is-moun/SKILL.md
skills/container-security/T1207-test-that-the-on-failure-container-restart-polic/SKILL.md
skills/container-security/T1209-verify-that-mount-propagation-mode-is-not-set-to/SKILL.md
skills/container-security/T1211-verify-that-seccomp-profile-is-enabled-docker/SKILL.md
skills/container-security/T1213-verify-that-cgroup-usage-is-confirmed-docker/SKILL.md
skills/container-security/T1215-verify-that-containers-are-restricted-from-acqui/SKILL.md
skills/input-validation/T122-test-for-remote-file-include/SKILL.md
skills/container-security/T1234-only-allow-trusted-users-to-control-the-docker-d/SKILL.md
skills/container-security/T1235-test-that-only-trusted-users-can-control-the-doc/SKILL.md
skills/container-security/T1236-audit-the-docker-daemon-and-its-files-docker/SKILL.md
skills/container-security/T1237-test-that-the-docker-daemon-and-its-files-are-au/SKILL.md
skills/authorization/T128-test-for-access-control-bypass-through-user-cont/SKILL.md
skills/api-security/T1363-verify-if-message-throttling-is-properly-perform/SKILL.md
skills/input-validation/T1392-test-for-server-side-request-forgery/SKILL.md
skills/cryptography/T1468-encrypt-sensitive-data-at-rest-in-the-browser/SKILL.md
skills/authorization/T15-centralize-authorization/SKILL.md
skills/authentication/T1539-clear-browser-data-on-user-logout/SKILL.md
skills/authentication/T1540-verify-that-browser-data-is-cleared-upon-user-lo/SKILL.md
skills/cryptography/T156-validate-certificate-and-its-chain-of-trust-prop/SKILL.md
skills/api-security/T167-test-that-the-application-is-not-vulnerable-to-j/SKILL.md
skills/cryptography/T175-test-that-the-client-validates-digital-certifica/SKILL.md
skills/authentication/T1889-secure-the-configuration-of-the-authorization-se/SKILL.md
skills/container-security/T1917-perform-container-security-assessment/SKILL.md
skills/authentication/T1918-integrate-with-sso/SKILL.md
skills/cryptography/T197-validate-the-signature-of-all-remote-code-update/SKILL.md
skills/authorization/T2105-enforce-the-use-of-client-certificate-bundles-fo/SKILL.md
skills/authorization/T2106-verify-that-the-use-of-client-certificate-bundle/SKILL.md
skills/container-security/T2109-enable-signed-image-enforcement-docker/SKILL.md
skills/container-security/T2110-verify-that-signed-image-enforcement-is-enabled/SKILL.md
skills/container-security/T2115-enable-image-vulnerability-scanning-docker/SKILL.md
skills/container-security/T2116-verify-that-image-vulnerability-scanning-is-enab/SKILL.md
skills/secrets-management/T214-protect-confidential-files-on-operating-system-o/SKILL.md
skills/api-security/T2140-test-that-apis-do-not-expose-sensitive-informati/SKILL.md
skills/container-security/T2256-authenticate-and-log-all-access-to-registries-co/SKILL.md
skills/container-security/T2257-regularly-update-and-patch-containerization-syst/SKILL.md
skills/infrastructure-hardening/T2258-minimize-host-os-attack-surface/SKILL.md
skills/authorization/T226-verify-that-authorization-is-centralized/SKILL.md
skills/authentication/T2276-test-to-confirm-that-authorization-and-authentic/SKILL.md
skills/authentication/T2277-test-to-confirm-the-use-of-an-account-and-identi/SKILL.md
skills/api-security/T228-test-that-application-restricts-http-message-siz/SKILL.md
skills/authorization/T2282-test-to-confirm-that-unauthenticated-parts-of-th/SKILL.md
skills/authentication/T230-test-that-server-to-server-system-accounts-meet/SKILL.md
skills/infrastructure-hardening/T2349-configure-software-to-have-secure-settings-by-de/SKILL.md
skills/infrastructure-hardening/T2357-verify-that-software-is-configured-to-have-secur/SKILL.md
skills/dependency-management/T241-verify-that-third-party-libraries-use-secure-set/SKILL.md
skills/cryptography/T2485-verify-that-remote-code-and-updates-are-correctl/SKILL.md
skills/cryptography/T2486-encrypt-and-sign-all-remote-code-updates-server/SKILL.md
skills/api-security/T2596-prevent-http-request-smuggling/SKILL.md
skills/authorization/T2597-implement-rbac-instead-of-individual-accounts/SKILL.md
skills/input-validation/T2599-protect-against-connection-string-parameter-poll/SKILL.md
skills/api-security/T2600-control-the-result-set-size-returned-by-a-query/SKILL.md
skills/cryptography/T2601-use-transparent-data-encryption-with-enterprise/SKILL.md
skills/database-security/T2602-log-typical-database-and-server-activities-and-r/SKILL.md
skills/cryptography/T2603-protect-backup-archive-bits/SKILL.md
skills/database-security/T2605-validate-database-traffic/SKILL.md
skills/authorization/T2606-verify-rbac-implemented-instead-of-individual-ac/SKILL.md
skills/authorization/T2607-verify-query-level-access-control-is-implemented/SKILL.md
skills/input-validation/T2608-verify-that-the-connection-string-is-protected-a/SKILL.md
skills/cryptography/T2610-verify-that-transparent-data-encryption-is-utili/SKILL.md
skills/database-security/T2611-verify-that-typical-database-and-server-activiti/SKILL.md
skills/cryptography/T2612-verify-backup-archive-bits-are-protected/SKILL.md
skills/database-security/T2614-verify-database-traffic-is-validated/SKILL.md
skills/database-security/T2615-limit-network-access-by-blocking-connections-fro/SKILL.md
skills/database-security/T2616-use-a-secure-authentication-mechanism-for-databa/SKILL.md
skills/database-security/T2619-ensure-that-row-level-security-is-correctly-conf/SKILL.md
skills/cryptography/T2620-protect-data-in-transit-with-tls-postgresql/SKILL.md
skills/cryptography/T2621-use-file-volume-encryption-and-consider-in-datab/SKILL.md
skills/database-security/T2652-consider-adding-plugins-for-stronger-authenticat/SKILL.md
skills/database-security/T2661-change-insecure-configuration-defaults-and-remov/SKILL.md
skills/database-security/T2662-restrict-network-access-to-the-database-server/SKILL.md
skills/database-security/T2663-use-a-secure-authentication-mechanism-for-databa/SKILL.md
skills/cryptography/T2665-protect-sensitive-data-at-rest-with-encryption/SKILL.md
skills/cryptography/T2666-protect-data-in-transit-with-tls-database-server/SKILL.md
skills/input-validation/T279-avoid-dynamically-loading-any-code-without-prope/SKILL.md
skills/infrastructure-hardening/T281-follow-best-practices-when-handling-access-token/SKILL.md
skills/infrastructure-hardening/T284-generate-secure-access-tokens-api-tokens/SKILL.md
skills/cryptography/T296-test-that-unencrypted-confidential-data-is-not-s/SKILL.md
skills/input-validation/T305-verify-that-your-application-dynamically-loads-c/SKILL.md
skills/api-security/T318-verify-security-of-cross-origin-resource-sharing/SKILL.md
skills/authentication/T323-test-that-default-accounts-are-disabled-or-defau/SKILL.md
skills/authentication/T340-use-an-account-and-identity-management-system/SKILL.md
skills/logging-monitoring/T349-protect-audit-information-and-logs-against-unaut/SKILL.md
skills/api-security/T35-fine-tune-http-server-settings/SKILL.md
skills/logging-monitoring/T350-verify-that-audit-information-is-sufficiently-pr/SKILL.md
skills/authorization/T373-design-and-regulate-access-to-unauthenticated-pa/SKILL.md
skills/api-security/T374-offload-http-request-handling-to-dedicated-modul/SKILL.md
skills/authorization/T378-authorize-every-request-for-data-objects/SKILL.md
skills/ci-cd-security/T3903-implement-application-and-webhook-security-strat/SKILL.md
skills/ci-cd-security/T3905-ensure-pipeline-efficiency-and-security-github/SKILL.md
skills/ci-cd-security/T3906-implement-secure-build-worker-management-github/SKILL.md
skills/ci-cd-security/T3907-ensure-pipeline-definition-and-security-github/SKILL.md
skills/ci-cd-security/T3908-enforce-artifact-signing-github/SKILL.md
skills/dependency-management/T3913-implement-package-registry-security-github/SKILL.md
skills/ci-cd-security/T3915-enforce-separation-of-deployment-configuration-f/SKILL.md
skills/ci-cd-security/T3916-ensure-automated-and-secure-deployment-github/SKILL.md
skills/ci-cd-security/T3920-test-application-and-webhook-security-strategies/SKILL.md
skills/ci-cd-security/T3922-test-pipeline-efficiency-and-security-github/SKILL.md
skills/ci-cd-security/T3923-test-secure-build-worker-management-github/SKILL.md
skills/ci-cd-security/T3924-test-pipeline-definition-and-security-github/SKILL.md
skills/ci-cd-security/T3925-test-artifact-signing-github/SKILL.md
skills/dependency-management/T3930-test-package-registry-security-github/SKILL.md
skills/ci-cd-security/T3932-test-separation-of-deployment-configuration-file/SKILL.md
skills/ci-cd-security/T3933-test-automated-and-secure-deployment-github/SKILL.md
skills/authentication/T395-verify-that-one-time-passwords-otp-are-securely/SKILL.md
skills/authentication/T406-secure-symmetric-key-authentication/SKILL.md
skills/authentication/T407-verify-that-symmetric-key-authentication-is-secu/SKILL.md
skills/cryptography/T439-verify-that-the-origin-and-integrity-of-remote-c/SKILL.md
skills/input-validation/T4433-prevent-path-environment-attacks-bash-shell/SKILL.md
skills/input-validation/T4436-protect-directory-writing-and-reading-bash-shell/SKILL.md
skills/input-validation/T4437-prevent-input-file-attacks-bash-shell/SKILL.md
skills/authentication/T4439-prevent-authentication-attacks-bash-shell/SKILL.md
skills/authorization/T4440-enforce-access-controls-bash-shell/SKILL.md
skills/infrastructure-hardening/T4441-prevent-attacks-related-to-environmental-vulnera/SKILL.md
skills/infrastructure-hardening/T4442-manage-and-protect-script-processes-bash-shell/SKILL.md
skills/cryptography/T4443-prevent-cryptographic-failures-bash-shell/SKILL.md
skills/input-validation/T4444-test-prevention-of-path-environment-attacks-bash/SKILL.md
skills/input-validation/T4447-test-directory-writing-and-reading-bash-shell/SKILL.md
skills/input-validation/T4448-test-prevention-against-input-file-attacks-bash/SKILL.md
skills/input-validation/T4449-test-prevention-of-file-upload-vulnerabilities-b/SKILL.md
skills/cryptography/T445-verify-that-only-approved-cryptographic-algorith/SKILL.md
skills/authentication/T4450-test-authentication-bash-shell/SKILL.md
skills/authorization/T4451-test-access-controls-bash-shell/SKILL.md
skills/infrastructure-hardening/T4452-test-environmental-vulnerabilities-bash-shell/SKILL.md
skills/infrastructure-hardening/T4453-test-protection-of-script-processes-bash-shell/SKILL.md
skills/cryptography/T4454-test-cryptographic-functions-bash-shell/SKILL.md
skills/cryptography/T446-verify-that-only-standard-libraries-are-used-for/SKILL.md
skills/infrastructure-hardening/T4601-prioritize-static-network-configuration/SKILL.md
skills/container-security/T4746-ensure-container-images-are-secure/SKILL.md
skills/container-security/T4747-limit-container-privileges/SKILL.md
skills/authorization/T4748-implement-role-based-access-control-rbac-for-con/SKILL.md
skills/container-security/T4749-monitor-containers-in-real-time/SKILL.md
skills/container-security/T4750-isolate-container-networks/SKILL.md
skills/container-security/T4751-reduce-the-attack-surface-of-container-images/SKILL.md
skills/api-security/T536-restrict-the-size-of-incoming-messages-in-servic/SKILL.md
skills/api-security/T537-test-that-the-size-of-incoming-messages-in-servi/SKILL.md
skills/authentication/T558-authenticate-all-other-components-before-any-net/SKILL.md
skills/input-validation/T573-prevent-uddi-ebxml-spoofing/SKILL.md
skills/input-validation/T576-verify-that-uddi-ebxml-spoofing-is-prevented/SKILL.md
skills/cryptography/T587-verify-that-cryptographically-secure-algorithms/SKILL.md
skills/authentication/T589-verify-that-all-the-components-are-authenticated/SKILL.md
skills/authentication/T61-disable-default-accounts-or-change-all-default-p/SKILL.md
skills/input-validation/T659-test-that-user-supplied-inputs-are-validated-bef/SKILL.md
skills/api-security/T66-prevent-web-pages-from-being-loaded-inside-ifram/SKILL.md
skills/authentication/T7353-authenticate-requests-with-signed-jwts-and-expli/SKILL.md
skills/authentication/T7354-hash-user-passwords-with-argon2-or-bcrypt-via-a/SKILL.md
skills/authorization/T7355-enforce-endpoint-authorization-with-dependencies/SKILL.md
skills/authorization/T7356-enforce-object-level-ownership-checks-on-every-r/SKILL.md
skills/api-security/T7357-drive-request-parsing-with-strict-pydantic-model/SKILL.md
skills/api-security/T7358-constrain-responses-with-response-model-to-preve/SKILL.md
skills/input-validation/T7359-prevent-sql-injection-with-orm-queries-and-param/SKILL.md
skills/input-validation/T7360-block-server-side-request-forgery-in-outbound-an/SKILL.md
skills/api-security/T7361-configure-cors-with-explicit-origins-and-never-w/SKILL.md
skills/api-security/T7362-enforce-trusted-hosts-and-https-only-transport-w/SKILL.md
skills/api-security/T7363-add-security-response-headers-via-middleware-fas/SKILL.md
skills/api-security/T7364-enforce-request-body-and-upload-size-limits-to-r/SKILL.md
skills/api-security/T7365-rate-limit-authentication-and-expensive-endpoint/SKILL.md
skills/input-validation/T7366-validate-and-safely-store-uploaded-files-fastapi/SKILL.md
skills/authentication/T7367-validate-the-origin-and-authenticate-every-webso/SKILL.md
skills/api-security/T7368-protect-cookie-authenticated-routes-with-samesit/SKILL.md
skills/secrets-management/T7369-externalize-the-jwt-signing-key-and-other-secret/SKILL.md
skills/api-security/T7370-return-generic-errors-and-disable-debug-output-i/SKILL.md
skills/logging-monitoring/T7371-emit-structured-audit-logs-without-leaking-sensi/SKILL.md
skills/api-security/T7372-restrict-interactive-api-documentation-exposure/SKILL.md
skills/api-security/T7373-trust-forwarded-headers-only-from-known-proxies/SKILL.md
skills/dependency-management/T7374-pin-hash-and-continuously-audit-python-dependenc/SKILL.md
skills/api-security/T7375-keep-blocking-work-off-the-async-event-loop-fast/SKILL.md
skills/api-security/T7376-add-automated-security-regression-tests-for-crit/SKILL.md
skills/input-validation/T7377-escape-and-sanitize-user-content-in-server-rende/SKILL.md
skills/input-validation/T7378-restrict-redirect-targets-to-relative-paths-or-a/SKILL.md
skills/api-security/T7379-serve-static-files-only-from-a-dedicated-non-sen/SKILL.md
skills/input-validation/T7380-avoid-os-command-and-dynamic-code-execution-on-u/SKILL.md
skills/input-validation/T7381-use-safe-parsers-and-never-deserialize-untrusted/SKILL.md
skills/api-security/T7382-make-critical-state-changing-operations-replay-r/SKILL.md
skills/input-validation/T7411-implement-controls-for-content-intended-to-be-di/SKILL.md
skills/input-validation/T7412-isolate-dangerous-functionality-and-risky-third/SKILL.md
skills/input-validation/T7414-verify-that-content-intended-as-text-is-rendered/SKILL.md
skills/input-validation/T7415-verify-that-dangerous-functionality-and-risky-th/SKILL.md
skills/authentication/T78-test-strength-of-password-reset-mechanism/SKILL.md
skills/authorization/T85-test-server-side-enforcement-of-authorization/SKILL.md
skills/authentication/T86-test-session-id-uniqueness-and-rotation-after-au/SKILL.md
skills/cryptography/T87-verify-that-all-data-in-transit-is-encrypted-usi/SKILL.md
skills/input-validation/T89-test-that-site-is-not-vulnerable-to-xss/SKILL.md
skills/api-security/T96-test-if-your-site-is-vulnerable-to-csrf/SKILL.md
skills/input-validation/T98-test-for-input-validation-on-a-server/SKILL.md
TMPLFILES
chk "template file violations" "$bad_tmpl" "0"

if [ -n "$FAIL" ]; then
  printf 'VERIFY FAIL:%b\n' "$FAIL"
  exit 1
fi
echo "VERIFY PASS"
