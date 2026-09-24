# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
# pyright: reportUnknownMemberType=false

import hashlib

from genlayer import *


DOMAIN_MANDATE_ID = hashlib.sha256(b"COVENANT/V1/MANDATE_ID").digest()
DOMAIN_MANDATE = hashlib.sha256(b"COVENANT/V1/MANDATE").digest()

POLICY_DETERMINISTIC = u256(1)
POLICY_EVIDENCE = u256(2)
POLICY_HUMAN = u256(3)

HUMAN_NONE = u256(0)
HUMAN_SINGLE_ADDRESS = u256(1)

ROLE_PRIMARY = u256(1)
ROLE_CORROBORATION = u256(2)
ROLE_BOTH = u256(3)

ZERO_ADDRESS_BYTES = b"\x00" * 20


def _hash(value: bytes) -> bytes:
    return hashlib.sha256(value).digest()


def _u256_bytes(value: u256) -> bytes:
    return int(value).to_bytes(32, byteorder="big", signed=False)


def _text_hash(value: str) -> bytes:
    return _hash(value.encode("utf-8"))


def _require_digest(value: bytes, field_name: str) -> None:
    if len(value) != 32:
        raise gl.vm.UserError(field_name + " must be exactly 32 bytes")


def _canonical_digest_list(
    values: list[bytes],
    field_name: str,
    require_non_empty: bool,
) -> list[bytes]:
    copied: list[bytes] = []

    for value in values:
        _require_digest(value, field_name)
        copied.append(value)

    if require_non_empty and len(copied) == 0:
        raise gl.vm.UserError(field_name + " must not be empty")

    copied.sort()

    index = 1
    while index < len(copied):
        if copied[index] == copied[index - 1]:
            raise gl.vm.UserError(field_name + " contains a duplicate commitment")
        index += 1

    return copied


def _mandate_key(mandate_id: bytes) -> str:
    _require_digest(mandate_id, "mandate_id")
    return mandate_id.hex()


def _version_key(mandate_id: bytes, version: u256) -> str:
    return _mandate_key(mandate_id) + ":" + str(int(version))


def _issuer_nonce_key(issuer: Address, issuer_nonce: u256) -> str:
    return issuer.as_hex + ":" + str(int(issuer_nonce))


def _authority_rule_hash(
    role_mask: u256,
    authority_id: bytes,
    publisher_name: str,
    source_prefix: str,
) -> bytes:
    return _hash(
        _u256_bytes(role_mask)
        + authority_id
        + _text_hash(publisher_name)
        + _text_hash(source_prefix)
    )


class CovenantMandates(gl.Contract):
    mandate_present: TreeMap[str, bool]
    mandate_issuers: TreeMap[str, Address]
    latest_versions: TreeMap[str, u256]
    issuer_nonce_used: TreeMap[str, bool]

    version_present: TreeMap[str, bool]
    version_eligible: TreeMap[str, bool]

    mandate_commitments: TreeMap[str, bytes]
    deterministic_policy_hashes: TreeMap[str, bytes]
    semantic_criteria_texts: TreeMap[str, str]
    semantic_criteria_hashes: TreeMap[str, bytes]
    evidence_policy_hashes: TreeMap[str, bytes]
    human_policy_hashes: TreeMap[str, bytes]
    risk_tiers: TreeMap[str, u256]

    max_values: TreeMap[str, u256]
    max_request_lifetimes: TreeMap[str, u256]
    repair_windows: TreeMap[str, u256]

    allowed_actions: TreeMap[str, DynArray[bytes]]
    allowed_targets: TreeMap[str, DynArray[bytes]]
    allowed_recipients: TreeMap[str, DynArray[bytes]]

    required_primary_counts: TreeMap[str, u256]
    required_corroboration_counts: TreeMap[str, u256]
    max_publication_ages: TreeMap[str, u256]
    max_observation_ages: TreeMap[str, u256]
    max_publish_observe_gaps: TreeMap[str, u256]
    max_evidence_records_values: TreeMap[str, u256]

    authority_role_masks: TreeMap[str, DynArray[u256]]
    authority_ids: TreeMap[str, DynArray[bytes]]
    authority_publisher_names: TreeMap[str, DynArray[str]]
    authority_source_prefixes: TreeMap[str, DynArray[str]]
    authority_rule_hashes: TreeMap[str, DynArray[bytes]]

    human_modes: TreeMap[str, u256]
    human_approvers: TreeMap[str, Address]

    def __init__(self) -> None:
        pass

    def _require_mandate(self, mandate_id: bytes) -> str:
        key = _mandate_key(mandate_id)
        if not self.mandate_present.get(key, False):
            raise gl.vm.UserError("unknown mandate")
        return key

    def _require_version(self, mandate_id: bytes, version: u256) -> str:
        self._require_mandate(mandate_id)
        key = _version_key(mandate_id, version)
        if not self.version_present.get(key, False):
            raise gl.vm.UserError("unknown mandate version")
        return key

    def _require_issuer(self, mandate_id: bytes) -> str:
        key = self._require_mandate(mandate_id)
        if gl.message.sender_address != self.mandate_issuers[key]:
            raise gl.vm.UserError("only the mandate issuer may perform this operation")
        return key

    def _store_bytes_array(self, key: str, values: list[bytes], target: TreeMap[str, DynArray[bytes]]) -> None:
        stored = target.get_or_insert_default(key)
        stored.clear()
        for value in values:
            stored.append(value)
        target[key] = stored

    def _store_u256_array(self, key: str, values: list[u256], target: TreeMap[str, DynArray[u256]]) -> None:
        stored = target.get_or_insert_default(key)
        stored.clear()
        for value in values:
            stored.append(value)
        target[key] = stored

    def _store_str_array(self, key: str, values: list[str], target: TreeMap[str, DynArray[str]]) -> None:
        stored = target.get_or_insert_default(key)
        stored.clear()
        for value in values:
            stored.append(value)
        target[key] = stored

    def _publish_version_data(
        self,
        mandate_id: bytes,
        version: u256,
        issuer: Address,
        max_value: u256,
        max_request_lifetime_seconds: u256,
        repair_window_seconds: u256,
        allowed_action_hashes: list[bytes],
        allowed_target_commitments: list[bytes],
        allowed_recipient_commitments: list[bytes],
        semantic_criteria: str,
        required_primary_count: u256,
        required_corroboration_count: u256,
        max_publication_age_seconds: u256,
        max_observation_age_seconds: u256,
        max_publish_observe_gap_seconds: u256,
        max_evidence_records: u256,
        authority_role_masks: list[u256],
        authority_ids: list[bytes],
        authority_publisher_names: list[str],
        authority_source_prefixes: list[str],
        human_mode: u256,
        human_approver: Address,
        risk_tier: u256,
    ) -> bytes:
        if int(max_request_lifetime_seconds) <= 0:
            raise gl.vm.UserError("max_request_lifetime_seconds must be positive")

        if int(repair_window_seconds) <= 0:
            raise gl.vm.UserError("repair_window_seconds must be positive")

        if int(repair_window_seconds) > int(max_request_lifetime_seconds):
            raise gl.vm.UserError("repair_window_seconds exceeds request lifetime")

        actions = _canonical_digest_list(
            allowed_action_hashes,
            "allowed_action_hashes",
            True,
        )

        targets = _canonical_digest_list(
            allowed_target_commitments,
            "allowed_target_commitments",
            False,
        )

        recipients = _canonical_digest_list(
            allowed_recipient_commitments,
            "allowed_recipient_commitments",
            False,
        )

        if semantic_criteria == "":
            raise gl.vm.UserError("semantic_criteria must not be empty")

        if int(required_primary_count) != 1:
            raise gl.vm.UserError("Covenant v1 requires exactly one primary authority")

        if int(max_publication_age_seconds) <= 0:
            raise gl.vm.UserError("max_publication_age_seconds must be positive")

        if int(max_observation_age_seconds) <= 0:
            raise gl.vm.UserError("max_observation_age_seconds must be positive")

        if int(max_publish_observe_gap_seconds) <= 0:
            raise gl.vm.UserError("max_publish_observe_gap_seconds must be positive")

        minimum_records = int(required_primary_count) + int(required_corroboration_count)

        if int(max_evidence_records) < minimum_records:
            raise gl.vm.UserError("max_evidence_records is below required authority count")

        rule_count = len(authority_ids)

        if rule_count == 0:
            raise gl.vm.UserError("at least one authority rule is required")

        if len(authority_role_masks) != rule_count:
            raise gl.vm.UserError("authority role-mask count mismatch")

        if len(authority_publisher_names) != rule_count:
            raise gl.vm.UserError("authority publisher-name count mismatch")

        if len(authority_source_prefixes) != rule_count:
            raise gl.vm.UserError("authority source-prefix count mismatch")

        rule_hashes: list[bytes] = []

        index = 0
        while index < rule_count:
            role_mask = authority_role_masks[index]
            authority_id = authority_ids[index]
            publisher_name = authority_publisher_names[index]
            source_prefix = authority_source_prefixes[index]

            if role_mask not in (ROLE_PRIMARY, ROLE_CORROBORATION, ROLE_BOTH):
                raise gl.vm.UserError("invalid authority role mask")

            _require_digest(authority_id, "authority_id")

            if publisher_name == "":
                raise gl.vm.UserError("publisher_name must not be empty")

            if not source_prefix.startswith("https://"):
                raise gl.vm.UserError("authority source prefix must begin with lowercase https://")

            if not source_prefix.endswith("/"):
                raise gl.vm.UserError("authority source prefix must end with /")

            for character in source_prefix:
                if character.isspace():
                    raise gl.vm.UserError("authority source prefix must contain no whitespace")

            rule_hashes.append(
                _authority_rule_hash(
                    role_mask,
                    authority_id,
                    publisher_name,
                    source_prefix,
                )
            )

            index += 1

        canonical_rule_hashes = _canonical_digest_list(
            rule_hashes,
            "authority_rule_hashes",
            True,
        )

        if human_mode == HUMAN_NONE:
            if human_approver.as_bytes != ZERO_ADDRESS_BYTES:
                raise gl.vm.UserError("human NONE mode requires zero approver address")
        elif human_mode == HUMAN_SINGLE_ADDRESS:
            if human_approver.as_bytes == ZERO_ADDRESS_BYTES:
                raise gl.vm.UserError("human SINGLE_ADDRESS mode requires non-zero approver")
        else:
            raise gl.vm.UserError("invalid human co-authorization mode")

        deterministic_preimage = (
            _u256_bytes(POLICY_DETERMINISTIC)
            + _u256_bytes(max_value)
            + _u256_bytes(max_request_lifetime_seconds)
            + _u256_bytes(repair_window_seconds)
            + _u256_bytes(u256(len(actions)))
            + b"".join(actions)
            + _u256_bytes(u256(len(targets)))
            + b"".join(targets)
            + _u256_bytes(u256(len(recipients)))
            + b"".join(recipients)
        )

        deterministic_policy_hash = _hash(deterministic_preimage)
        semantic_criteria_hash = _text_hash(semantic_criteria)

        evidence_preimage = (
            _u256_bytes(POLICY_EVIDENCE)
            + _u256_bytes(required_primary_count)
            + _u256_bytes(required_corroboration_count)
            + _u256_bytes(max_publication_age_seconds)
            + _u256_bytes(max_observation_age_seconds)
            + _u256_bytes(max_publish_observe_gap_seconds)
            + _u256_bytes(max_evidence_records)
            + _u256_bytes(u256(len(canonical_rule_hashes)))
            + b"".join(canonical_rule_hashes)
        )

        evidence_policy_hash = _hash(evidence_preimage)

        human_preimage = (
            _u256_bytes(POLICY_HUMAN)
            + _u256_bytes(human_mode)
            + human_approver.as_bytes
        )

        human_policy_hash = _hash(human_preimage)

        mandate_preimage = (
            DOMAIN_MANDATE
            + _u256_bytes(gl.message.chain_id)
            + gl.message.contract_address.as_bytes
            + mandate_id
            + _u256_bytes(version)
            + issuer.as_bytes
            + deterministic_policy_hash
            + semantic_criteria_hash
            + evidence_policy_hash
            + _u256_bytes(risk_tier)
            + human_policy_hash
        )

        mandate_commitment = _hash(mandate_preimage)
        key = _version_key(mandate_id, version)

        if self.version_present.get(key, False):
            raise gl.vm.UserError("mandate version already exists")

        self.version_present[key] = True
        self.version_eligible[key] = True

        self.mandate_commitments[key] = mandate_commitment
        self.deterministic_policy_hashes[key] = deterministic_policy_hash
        self.semantic_criteria_texts[key] = semantic_criteria
        self.semantic_criteria_hashes[key] = semantic_criteria_hash
        self.evidence_policy_hashes[key] = evidence_policy_hash
        self.human_policy_hashes[key] = human_policy_hash
        self.risk_tiers[key] = risk_tier

        self.max_values[key] = max_value
        self.max_request_lifetimes[key] = max_request_lifetime_seconds
        self.repair_windows[key] = repair_window_seconds

        self._store_bytes_array(key, actions, self.allowed_actions)
        self._store_bytes_array(key, targets, self.allowed_targets)
        self._store_bytes_array(key, recipients, self.allowed_recipients)

        self.required_primary_counts[key] = required_primary_count
        self.required_corroboration_counts[key] = required_corroboration_count
        self.max_publication_ages[key] = max_publication_age_seconds
        self.max_observation_ages[key] = max_observation_age_seconds
        self.max_publish_observe_gaps[key] = max_publish_observe_gap_seconds
        self.max_evidence_records_values[key] = max_evidence_records

        self._store_u256_array(key, authority_role_masks, self.authority_role_masks)
        self._store_bytes_array(key, authority_ids, self.authority_ids)
        self._store_str_array(key, authority_publisher_names, self.authority_publisher_names)
        self._store_str_array(key, authority_source_prefixes, self.authority_source_prefixes)
        self._store_bytes_array(key, rule_hashes, self.authority_rule_hashes)

        self.human_modes[key] = human_mode
        self.human_approvers[key] = human_approver

        return mandate_commitment

    @gl.public.write
    def create_mandate(
        self,
        issuer_nonce: u256,
        max_value: u256,
        max_request_lifetime_seconds: u256,
        repair_window_seconds: u256,
        allowed_action_hashes: list[bytes],
        allowed_target_commitments: list[bytes],
        allowed_recipient_commitments: list[bytes],
        semantic_criteria: str,
        required_primary_count: u256,
        required_corroboration_count: u256,
        max_publication_age_seconds: u256,
        max_observation_age_seconds: u256,
        max_publish_observe_gap_seconds: u256,
        max_evidence_records: u256,
        authority_role_masks: list[u256],
        authority_ids: list[bytes],
        authority_publisher_names: list[str],
        authority_source_prefixes: list[str],
        human_mode: u256,
        human_approver: Address,
        risk_tier: u256,
    ) -> bytes:
        issuer = gl.message.sender_address
        nonce_key = _issuer_nonce_key(issuer, issuer_nonce)

        if self.issuer_nonce_used.get(nonce_key, False):
            raise gl.vm.UserError("issuer nonce already used")

        mandate_id = _hash(
            DOMAIN_MANDATE_ID
            + _u256_bytes(gl.message.chain_id)
            + gl.message.contract_address.as_bytes
            + issuer.as_bytes
            + _u256_bytes(issuer_nonce)
        )

        mandate_key = _mandate_key(mandate_id)

        if self.mandate_present.get(mandate_key, False):
            raise gl.vm.UserError("mandate identifier collision")

        self._publish_version_data(
            mandate_id,
            u256(1),
            issuer,
            max_value,
            max_request_lifetime_seconds,
            repair_window_seconds,
            allowed_action_hashes,
            allowed_target_commitments,
            allowed_recipient_commitments,
            semantic_criteria,
            required_primary_count,
            required_corroboration_count,
            max_publication_age_seconds,
            max_observation_age_seconds,
            max_publish_observe_gap_seconds,
            max_evidence_records,
            authority_role_masks,
            authority_ids,
            authority_publisher_names,
            authority_source_prefixes,
            human_mode,
            human_approver,
            risk_tier,
        )

        self.issuer_nonce_used[nonce_key] = True
        self.mandate_present[mandate_key] = True
        self.mandate_issuers[mandate_key] = issuer
        self.latest_versions[mandate_key] = u256(1)

        return mandate_id

    @gl.public.write
    def publish_next_version(
        self,
        mandate_id: bytes,
        max_value: u256,
        max_request_lifetime_seconds: u256,
        repair_window_seconds: u256,
        allowed_action_hashes: list[bytes],
        allowed_target_commitments: list[bytes],
        allowed_recipient_commitments: list[bytes],
        semantic_criteria: str,
        required_primary_count: u256,
        required_corroboration_count: u256,
        max_publication_age_seconds: u256,
        max_observation_age_seconds: u256,
        max_publish_observe_gap_seconds: u256,
        max_evidence_records: u256,
        authority_role_masks: list[u256],
        authority_ids: list[bytes],
        authority_publisher_names: list[str],
        authority_source_prefixes: list[str],
        human_mode: u256,
        human_approver: Address,
        risk_tier: u256,
    ) -> u256:
        mandate_key = self._require_issuer(mandate_id)
        issuer = self.mandate_issuers[mandate_key]
        next_version = u256(int(self.latest_versions[mandate_key]) + 1)

        self._publish_version_data(
            mandate_id,
            next_version,
            issuer,
            max_value,
            max_request_lifetime_seconds,
            repair_window_seconds,
            allowed_action_hashes,
            allowed_target_commitments,
            allowed_recipient_commitments,
            semantic_criteria,
            required_primary_count,
            required_corroboration_count,
            max_publication_age_seconds,
            max_observation_age_seconds,
            max_publish_observe_gap_seconds,
            max_evidence_records,
            authority_role_masks,
            authority_ids,
            authority_publisher_names,
            authority_source_prefixes,
            human_mode,
            human_approver,
            risk_tier,
        )

        self.latest_versions[mandate_key] = next_version
        return next_version

    @gl.public.write
    def set_version_eligible(
        self,
        mandate_id: bytes,
        version: u256,
        eligible: bool,
    ) -> None:
        self._require_issuer(mandate_id)
        key = self._require_version(mandate_id, version)
        self.version_eligible[key] = eligible

    @gl.public.view
    def get_contract_address(self) -> str:
        return str(gl.message.contract_address)

    @gl.public.view
    def get_chain_id(self) -> u256:
        return gl.message.chain_id

    @gl.public.view
    def mandate_exists(self, mandate_id: bytes) -> bool:
        return self.mandate_present.get(_mandate_key(mandate_id), False)

    @gl.public.view
    def get_issuer(self, mandate_id: bytes) -> str:
        key = self._require_mandate(mandate_id)
        return str(self.mandate_issuers[key])

    @gl.public.view
    def get_latest_version(self, mandate_id: bytes) -> u256:
        key = self._require_mandate(mandate_id)
        return self.latest_versions[key]

    @gl.public.view
    def version_exists(self, mandate_id: bytes, version: u256) -> bool:
        self._require_mandate(mandate_id)
        return self.version_present.get(_version_key(mandate_id, version), False)

    @gl.public.view
    def is_version_eligible(self, mandate_id: bytes, version: u256) -> bool:
        key = self._require_version(mandate_id, version)
        return self.version_eligible[key]

    @gl.public.view
    def get_mandate_commitment(self, mandate_id: bytes, version: u256) -> bytes:
        key = self._require_version(mandate_id, version)
        return self.mandate_commitments[key]

    @gl.public.view
    def get_deterministic_policy_hash(self, mandate_id: bytes, version: u256) -> bytes:
        key = self._require_version(mandate_id, version)
        return self.deterministic_policy_hashes[key]

    @gl.public.view
    def get_semantic_criteria(self, mandate_id: bytes, version: u256) -> str:
        key = self._require_version(mandate_id, version)
        return self.semantic_criteria_texts[key]

    @gl.public.view
    def get_semantic_criteria_hash(self, mandate_id: bytes, version: u256) -> bytes:
        key = self._require_version(mandate_id, version)
        return self.semantic_criteria_hashes[key]

    @gl.public.view
    def get_evidence_policy_hash(self, mandate_id: bytes, version: u256) -> bytes:
        key = self._require_version(mandate_id, version)
        return self.evidence_policy_hashes[key]

    @gl.public.view
    def get_human_policy_hash(self, mandate_id: bytes, version: u256) -> bytes:
        key = self._require_version(mandate_id, version)
        return self.human_policy_hashes[key]

    @gl.public.view
    def get_risk_tier(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.risk_tiers[key]

    @gl.public.view
    def get_max_value(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.max_values[key]

    @gl.public.view
    def get_max_request_lifetime_seconds(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.max_request_lifetimes[key]

    @gl.public.view
    def get_repair_window_seconds(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.repair_windows[key]

    @gl.public.view
    def get_allowed_action_hashes(self, mandate_id: bytes, version: u256) -> DynArray[bytes]:
        key = self._require_version(mandate_id, version)
        return self.allowed_actions[key]

    @gl.public.view
    def get_allowed_target_commitments(self, mandate_id: bytes, version: u256) -> DynArray[bytes]:
        key = self._require_version(mandate_id, version)
        return self.allowed_targets[key]

    @gl.public.view
    def get_allowed_recipient_commitments(self, mandate_id: bytes, version: u256) -> DynArray[bytes]:
        key = self._require_version(mandate_id, version)
        return self.allowed_recipients[key]

    @gl.public.view
    def get_required_primary_count(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.required_primary_counts[key]

    @gl.public.view
    def get_required_corroboration_count(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.required_corroboration_counts[key]

    @gl.public.view
    def get_max_publication_age_seconds(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.max_publication_ages[key]

    @gl.public.view
    def get_max_observation_age_seconds(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.max_observation_ages[key]

    @gl.public.view
    def get_max_publish_observe_gap_seconds(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.max_publish_observe_gaps[key]

    @gl.public.view
    def get_max_evidence_records(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.max_evidence_records_values[key]

    @gl.public.view
    def get_authority_role_masks(self, mandate_id: bytes, version: u256) -> DynArray[u256]:
        key = self._require_version(mandate_id, version)
        return self.authority_role_masks[key]

    @gl.public.view
    def get_authority_ids(self, mandate_id: bytes, version: u256) -> DynArray[bytes]:
        key = self._require_version(mandate_id, version)
        return self.authority_ids[key]

    @gl.public.view
    def get_authority_publisher_names(self, mandate_id: bytes, version: u256) -> DynArray[str]:
        key = self._require_version(mandate_id, version)
        return self.authority_publisher_names[key]

    @gl.public.view
    def get_authority_source_prefixes(self, mandate_id: bytes, version: u256) -> DynArray[str]:
        key = self._require_version(mandate_id, version)
        return self.authority_source_prefixes[key]

    @gl.public.view
    def get_authority_rule_hashes(self, mandate_id: bytes, version: u256) -> DynArray[bytes]:
        key = self._require_version(mandate_id, version)
        return self.authority_rule_hashes[key]

    @gl.public.view
    def get_human_mode(self, mandate_id: bytes, version: u256) -> u256:
        key = self._require_version(mandate_id, version)
        return self.human_modes[key]

    @gl.public.view
    def get_human_approver(self, mandate_id: bytes, version: u256) -> str:
        key = self._require_version(mandate_id, version)
        return str(self.human_approvers[key])
