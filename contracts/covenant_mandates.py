# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# pyright: reportUnknownMemberType=false

import hashlib
import typing
from genlayer import *
DOMAIN_MANDATE_ID=hashlib.sha256(b"COVENANT/V1/MANDATE_ID").digest()
DOMAIN_MANDATE=hashlib.sha256(b"COVENANT/V1/MANDATE").digest()
POLICY_DETERMINISTIC=u256(1)
POLICY_EVIDENCE=u256(2)
POLICY_HUMAN=u256(3)
HUMAN_NONE=u256(0)
HUMAN_SINGLE_ADDRESS=u256(1)
ROLE_PRIMARY=u256(1)
ROLE_CORROBORATION=u256(2)
ROLE_BOTH=u256(3)
ZERO_ADDRESS_BYTES=b"\x00"*20
MAX_EVIDENCE_BODY_BYTES=8192
MAX_SEMANTIC_CRITERIA_BYTES=4096
MAX_AUTHORITY_PUBLISHER_NAME_BYTES=256
MAX_AUTHORITY_SOURCE_PREFIX_BYTES=2048
MAX_POLICY_COLLECTION_ITEMS=8
MAX_EVIDENCE_RECORDS=8
def _hash(value:bytes)->bytes:
    return hashlib.sha256(value).digest()
def _u256_bytes(value:u256)->bytes:
    return int(value).to_bytes(32,byteorder="big",signed=False)
def _text_hash(value:str)->bytes:
    return _hash(value.encode("utf-8"))
def _require_text_limit(value:str,field_name:str,maximum:int)->None:
    if len(value.encode("utf-8"))>maximum:
        raise gl.vm.UserError(field_name+" exceeds protocol size limit")
def _require_positive(value:u256,field_name:str)->None:
    if int(value)<=0:
        raise gl.vm.UserError(field_name+" must be positive")
def _require_collection_limit(values:typing.Any,field_name:str)->None:
    if len(values)>MAX_POLICY_COLLECTION_ITEMS:
        raise gl.vm.UserError(field_name+" exceeds protocol item limit")
def _safe_https_reference(value:str,require_trailing_slash:bool)->bool:
    if not value.startswith("https://"):
        return False
    if any(c in value for c in ("\\","?","#","%")):
        return False
    rest=value[8:]
    slash=rest.find("/")
    if slash<=0:
        return False
    authority=rest[:slash]
    if "@" in authority or any(c.isspace() for c in authority):
        return False
    path=value[8+slash:]
    if require_trailing_slash and not path.endswith("/"):
        return False
    for segment in path.split("/"):
        if segment in (".",".."):
            return False
    return True
def _require_digest(value:bytes,field_name:str)->None:
    if len(value)!=32:
        raise gl.vm.UserError(field_name+" must be exactly 32 bytes")
def _canonical_digest_list(values:list[bytes],field_name:str,require_non_empty:bool)->list[bytes]:
    copied:list[bytes]=[]
    for value in values:
        _require_digest(value,field_name)
        copied.append(value)
    if require_non_empty and len(copied)==0:
        raise gl.vm.UserError(field_name+" must not be empty")
    copied.sort()
    index=1
    while index<len(copied):
        if copied[index]==copied[index-1]:
            raise gl.vm.UserError(field_name+" contains a duplicate commitment")
        index+=1
    return copied
def _mandate_key(mandate_id:bytes)->str:
    _require_digest(mandate_id,"mandate_id")
    return mandate_id.hex()
def _version_key(mandate_id:bytes,version:u256)->str:
    return _mandate_key(mandate_id)+":"+str(int(version))
def _issuer_nonce_key(issuer:Address,issuer_nonce:u256)->str:
    return issuer.as_hex+":"+str(int(issuer_nonce))
def _authority_rule_hash(role_mask:u256,authority_id:bytes,publisher_name:str,source_prefix:str)->bytes:
    return _hash(_u256_bytes(role_mask)+authority_id+_text_hash(publisher_name)+_text_hash(source_prefix))
class CovenantMandates(gl.Contract):
    a:TreeMap[str,bool]
    b:TreeMap[str,Address]
    c:TreeMap[str,u256]
    d:TreeMap[str,bool]
    e:TreeMap[str,bool]
    f:TreeMap[str,bool]
    g:TreeMap[str,bytes]
    h:TreeMap[str,bytes]
    i:TreeMap[str,str]
    j:TreeMap[str,bytes]
    k:TreeMap[str,bytes]
    l:TreeMap[str,bytes]
    m:TreeMap[str,u256]
    n:TreeMap[str,u256]
    o:TreeMap[str,u256]
    p:TreeMap[str,u256]
    q:TreeMap[str,DynArray[bytes]]
    r:TreeMap[str,DynArray[bytes]]
    s:TreeMap[str,DynArray[bytes]]
    t:TreeMap[str,u256]
    u:TreeMap[str,u256]
    v:TreeMap[str,u256]
    w:TreeMap[str,u256]
    x:TreeMap[str,u256]
    y:TreeMap[str,u256]
    z:TreeMap[str,u256]
    aa:TreeMap[str,DynArray[u256]]
    ab:TreeMap[str,DynArray[bytes]]
    ac:TreeMap[str,DynArray[str]]
    ad:TreeMap[str,DynArray[str]]
    ae:TreeMap[str,DynArray[bytes]]
    af:TreeMap[str,u256]
    ag:TreeMap[str,Address]
    def __init__(self)->None:
        pass
    def _require_mandate(self,mandate_id:bytes)->str:
        key=_mandate_key(mandate_id)
        if not self.a.get(key,False):
            raise gl.vm.UserError("unknown mandate")
        return key
    def _require_version(self,mandate_id:bytes,version:u256)->str:
        self._require_mandate(mandate_id)
        key=_version_key(mandate_id,version)
        if not self.e.get(key,False):
            raise gl.vm.UserError("unknown mandate version")
        return key
    def _require_issuer(self,mandate_id:bytes)->str:
        key=self._require_mandate(mandate_id)
        if gl.message.sender_address!=self.b[key]:
            raise gl.vm.UserError("only the mandate issuer may perform this operation")
        return key
    def _version_value(self,mandate_id:bytes,version:u256,target:typing.Any)->typing.Any:
        return target[self._require_version(mandate_id,version)]
    def _store_array(self,key:str,values:typing.Any,target:typing.Any)->None:
        stored=target.get_or_insert_default(key)
        for value in values:
            stored.append(value)
        target[key]=stored
    def _publish_version_data(self,a:bytes,b:u256,c:Address,d:u256,e:u256,f:u256,g:list[bytes],h:list[bytes],i:list[bytes],j:str,k:u256,l:u256,m:u256,n:u256,o:u256,p:u256,q:u256,r:list[u256],s:list[bytes],t:list[str],u:list[str],v:u256,w:Address,x:u256)->bytes:
        _require_positive(e,"max_request_lifetime_seconds")
        _require_positive(f,"repair_window_seconds")
        if int(f)>int(e):
            raise gl.vm.UserError("repair_window_seconds exceeds request lifetime")
        _require_collection_limit(g,"allowed_action_hashes")
        _require_collection_limit(h,"allowed_target_commitments")
        _require_collection_limit(i,"allowed_recipient_commitments")
        actions=_canonical_digest_list(g,"allowed_action_hashes",True,)
        targets=_canonical_digest_list(h,"allowed_target_commitments",False,)
        recipients=_canonical_digest_list(i,"allowed_recipient_commitments",False,)
        if j=="":
            raise gl.vm.UserError("semantic_criteria must not be empty")
        _require_text_limit(j,"semantic_criteria",MAX_SEMANTIC_CRITERIA_BYTES,)
        _require_positive(q,"max_evidence_body_bytes")
        if int(q)>MAX_EVIDENCE_BODY_BYTES:
            raise gl.vm.UserError("max_evidence_body_bytes exceeds protocol limit")
        if int(k)!=1:
            raise gl.vm.UserError("Covenant v1 requires exactly one primary authority")
        for value,field_name in((m,"max_publication_age_seconds"),(n,"max_observation_age_seconds"),(o,"max_publish_observe_gap_seconds")):
            _require_positive(value,field_name)
        minimum_records=int(k)+int(l)
        if int(p)<minimum_records:
            raise gl.vm.UserError("max_evidence_records is below required authority count")
        if int(p)>MAX_EVIDENCE_RECORDS:
            raise gl.vm.UserError("max_evidence_records exceeds protocol limit")
        _require_collection_limit(r,"authority_role_masks")
        _require_collection_limit(s,"authority_ids")
        _require_collection_limit(t,"authority_publisher_names")
        _require_collection_limit(u,"authority_source_prefixes")
        rule_count=len(s)
        if rule_count==0:
            raise gl.vm.UserError("at least one authority rule is required")
        for values,error in((r,"authority role-mask count mismatch"),(t,"authority publisher-name count mismatch"),(u,"authority source-prefix count mismatch")):
            if len(values)!=rule_count:
                raise gl.vm.UserError(error)
        rule_hashes:list[bytes]=[]
        index=0
        while index<rule_count:
            role_mask=r[index]
            authority_id=s[index]
            publisher_name=t[index]
            source_prefix=u[index]
            if role_mask not in(ROLE_PRIMARY,ROLE_CORROBORATION,ROLE_BOTH):
                raise gl.vm.UserError("invalid authority role mask")
            _require_digest(authority_id,"authority_id")
            if publisher_name=="":
                raise gl.vm.UserError("publisher_name must not be empty")
            _require_text_limit(publisher_name,"publisher_name",MAX_AUTHORITY_PUBLISHER_NAME_BYTES,)
            _require_text_limit(source_prefix,"authority source prefix",MAX_AUTHORITY_SOURCE_PREFIX_BYTES,)
            if not _safe_https_reference(source_prefix,True):
                raise gl.vm.UserError("authority source prefix is not canonical safe HTTPS")
            rule_hashes.append(_authority_rule_hash(role_mask,authority_id,publisher_name,source_prefix,))
            index+=1
        canonical_rule_hashes=_canonical_digest_list(rule_hashes,"authority_rule_hashes",True,)
        if v==HUMAN_NONE:
            if w.as_bytes!=ZERO_ADDRESS_BYTES:
                raise gl.vm.UserError("human NONE mode requires zero approver address")
        elif v==HUMAN_SINGLE_ADDRESS:
            if w.as_bytes==ZERO_ADDRESS_BYTES:
                raise gl.vm.UserError("human SINGLE_ADDRESS mode requires non-zero approver")
        else:
            raise gl.vm.UserError("invalid human co-authorization mode")
        deterministic_preimage=(_u256_bytes(POLICY_DETERMINISTIC)+_u256_bytes(d)+_u256_bytes(e)+_u256_bytes(f)+_u256_bytes(u256(len(actions)))+b"".join(actions)+_u256_bytes(u256(len(targets)))+b"".join(targets)+_u256_bytes(u256(len(recipients)))+b"".join(recipients))
        deterministic_policy_hash=_hash(deterministic_preimage)
        semantic_criteria_hash=_text_hash(j)
        evidence_preimage=(_u256_bytes(POLICY_EVIDENCE)+_u256_bytes(k)+_u256_bytes(l)+_u256_bytes(m)+_u256_bytes(n)+_u256_bytes(o)+_u256_bytes(p)+_u256_bytes(q)+_u256_bytes(u256(len(canonical_rule_hashes)))+b"".join(canonical_rule_hashes))
        evidence_policy_hash=_hash(evidence_preimage)
        human_preimage=(_u256_bytes(POLICY_HUMAN)+_u256_bytes(v)+w.as_bytes)
        human_policy_hash=_hash(human_preimage)
        mandate_preimage=(DOMAIN_MANDATE+_u256_bytes(gl.message.chain_id)+gl.message.contract_address.as_bytes+a+_u256_bytes(b)+c.as_bytes+deterministic_policy_hash+semantic_criteria_hash+evidence_policy_hash+_u256_bytes(x)+human_policy_hash)
        mandate_commitment=_hash(mandate_preimage)
        key=_version_key(a,b)
        if self.e.get(key,False):
            raise gl.vm.UserError("mandate version already exists")
        self.e[key]=True
        self.f[key]=True
        self.g[key]=mandate_commitment
        self.h[key]=deterministic_policy_hash
        self.i[key]=j
        self.j[key]=semantic_criteria_hash
        self.k[key]=evidence_policy_hash
        self.l[key]=human_policy_hash
        self.m[key]=x
        self.n[key]=d
        self.o[key]=e
        self.p[key]=f
        self._store_array(key,actions,self.q)
        self._store_array(key,targets,self.r)
        self._store_array(key,recipients,self.s)
        self.t[key]=k
        self.u[key]=l
        self.v[key]=m
        self.w[key]=n
        self.x[key]=o
        self.y[key]=p
        self.z[key]=q
        self._store_array(key,r,self.aa)
        self._store_array(key,s,self.ab)
        self._store_array(key,t,self.ac)
        self._store_array(key,u,self.ad)
        self._store_array(key,rule_hashes,self.ae)
        self.af[key]=v
        self.ag[key]=w
        return mandate_commitment
    @gl.public.write
    def create_mandate(self,issuer_nonce:u256,max_value:u256,max_request_lifetime_seconds:u256,repair_window_seconds:u256,allowed_action_hashes:list[bytes],allowed_target_commitments:list[bytes],allowed_recipient_commitments:list[bytes],semantic_criteria:str,required_primary_count:u256,required_corroboration_count:u256,max_publication_age_seconds:u256,max_observation_age_seconds:u256,max_publish_observe_gap_seconds:u256,max_evidence_records:u256,max_evidence_body_bytes:u256,authority_role_masks:list[u256],authority_ids:list[bytes],authority_publisher_names:list[str],authority_source_prefixes:list[str],human_mode:u256,human_approver:Address,risk_tier:u256,)->bytes:
        issuer=gl.message.sender_address
        nonce_key=_issuer_nonce_key(issuer,issuer_nonce)
        if self.d.get(nonce_key,False):
            raise gl.vm.UserError("issuer nonce already used")
        mandate_id=_hash(DOMAIN_MANDATE_ID+_u256_bytes(gl.message.chain_id)+gl.message.contract_address.as_bytes+issuer.as_bytes+_u256_bytes(issuer_nonce))
        mandate_key=_mandate_key(mandate_id)
        if self.a.get(mandate_key,False):
            raise gl.vm.UserError("mandate identifier collision")
        self._publish_version_data(mandate_id,u256(1),issuer,max_value,max_request_lifetime_seconds,repair_window_seconds,allowed_action_hashes,allowed_target_commitments,allowed_recipient_commitments,semantic_criteria,required_primary_count,required_corroboration_count,max_publication_age_seconds,max_observation_age_seconds,max_publish_observe_gap_seconds,max_evidence_records,max_evidence_body_bytes,authority_role_masks,authority_ids,authority_publisher_names,authority_source_prefixes,human_mode,human_approver,risk_tier,)
        self.d[nonce_key]=True
        self.a[mandate_key]=True
        self.b[mandate_key]=issuer
        self.c[mandate_key]=u256(1)
        return mandate_id
    @gl.public.write
    def publish_next_version(self,mandate_id:bytes,max_value:u256,max_request_lifetime_seconds:u256,repair_window_seconds:u256,allowed_action_hashes:list[bytes],allowed_target_commitments:list[bytes],allowed_recipient_commitments:list[bytes],semantic_criteria:str,required_primary_count:u256,required_corroboration_count:u256,max_publication_age_seconds:u256,max_observation_age_seconds:u256,max_publish_observe_gap_seconds:u256,max_evidence_records:u256,max_evidence_body_bytes:u256,authority_role_masks:list[u256],authority_ids:list[bytes],authority_publisher_names:list[str],authority_source_prefixes:list[str],human_mode:u256,human_approver:Address,risk_tier:u256,)->u256:
        mandate_key=self._require_issuer(mandate_id)
        issuer=self.b[mandate_key]
        next_version=u256(int(self.c[mandate_key])+1)
        self._publish_version_data(mandate_id,next_version,issuer,max_value,max_request_lifetime_seconds,repair_window_seconds,allowed_action_hashes,allowed_target_commitments,allowed_recipient_commitments,semantic_criteria,required_primary_count,required_corroboration_count,max_publication_age_seconds,max_observation_age_seconds,max_publish_observe_gap_seconds,max_evidence_records,max_evidence_body_bytes,authority_role_masks,authority_ids,authority_publisher_names,authority_source_prefixes,human_mode,human_approver,risk_tier,)
        self.c[mandate_key]=next_version
        return next_version
    @gl.public.write
    def set_version_eligible(self,mandate_id:bytes,version:u256,eligible:bool,)->None:
        self._require_issuer(mandate_id)
        key=self._require_version(mandate_id,version)
        self.f[key]=eligible
    @gl.public.view
    def get_contract_address(self)->str:
        return str(gl.message.contract_address)
    @gl.public.view
    def get_chain_id(self)->u256:
        return gl.message.chain_id
    @gl.public.view
    def mandate_exists(self,mandate_id:bytes)->bool:
        return self.a.get(_mandate_key(mandate_id),False)
    @gl.public.view
    def get_issuer(self,mandate_id:bytes)->str:
        key=self._require_mandate(mandate_id)
        return str(self.b[key])
    @gl.public.view
    def get_latest_version(self,mandate_id:bytes)->u256:
        key=self._require_mandate(mandate_id)
        return self.c[key]
    @gl.public.view
    def version_exists(self,mandate_id:bytes,version:u256)->bool:
        self._require_mandate(mandate_id)
        return self.e.get(_version_key(mandate_id,version),False)
    @gl.public.view
    def is_version_eligible(self,mandate_id:bytes,version:u256)->bool:
        return self._version_value(mandate_id,version,self.f)
    @gl.public.view
    def get_mandate_commitment(self,mandate_id:bytes,version:u256)->bytes:
        return self._version_value(mandate_id,version,self.g)
    @gl.public.view
    def get_deterministic_policy_hash(self,mandate_id:bytes,version:u256)->bytes:
        return self._version_value(mandate_id,version,self.h)
    @gl.public.view
    def get_semantic_criteria(self,mandate_id:bytes,version:u256)->str:
        return self._version_value(mandate_id,version,self.i)
    @gl.public.view
    def get_semantic_criteria_hash(self,mandate_id:bytes,version:u256)->bytes:
        return self._version_value(mandate_id,version,self.j)
    @gl.public.view
    def get_evidence_policy_hash(self,mandate_id:bytes,version:u256)->bytes:
        return self._version_value(mandate_id,version,self.k)
    @gl.public.view
    def get_human_policy_hash(self,mandate_id:bytes,version:u256)->bytes:
        return self._version_value(mandate_id,version,self.l)
    @gl.public.view
    def get_risk_tier(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.m)
    @gl.public.view
    def get_max_value(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.n)
    @gl.public.view
    def get_max_request_lifetime_seconds(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.o)
    @gl.public.view
    def get_repair_window_seconds(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.p)
    @gl.public.view
    def get_allowed_action_hashes(self,mandate_id:bytes,version:u256)->DynArray[bytes]:
        return self._version_value(mandate_id,version,self.q)
    @gl.public.view
    def get_allowed_target_commitments(self,mandate_id:bytes,version:u256)->DynArray[bytes]:
        return self._version_value(mandate_id,version,self.r)
    @gl.public.view
    def get_allowed_recipient_commitments(self,mandate_id:bytes,version:u256)->DynArray[bytes]:
        return self._version_value(mandate_id,version,self.s)
    @gl.public.view
    def get_required_primary_count(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.t)
    @gl.public.view
    def get_required_corroboration_count(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.u)
    @gl.public.view
    def get_max_publication_age_seconds(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.v)
    @gl.public.view
    def get_max_observation_age_seconds(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.w)
    @gl.public.view
    def get_max_publish_observe_gap_seconds(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.x)
    @gl.public.view
    def get_max_evidence_records(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.y)
    @gl.public.view
    def get_max_evidence_body_bytes(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.z)
    @gl.public.view
    def get_authority_role_masks(self,mandate_id:bytes,version:u256)->DynArray[u256]:
        return self._version_value(mandate_id,version,self.aa)
    @gl.public.view
    def get_authority_ids(self,mandate_id:bytes,version:u256)->DynArray[bytes]:
        return self._version_value(mandate_id,version,self.ab)
    @gl.public.view
    def get_authority_publisher_names(self,mandate_id:bytes,version:u256)->DynArray[str]:
        return self._version_value(mandate_id,version,self.ac)
    @gl.public.view
    def get_authority_source_prefixes(self,mandate_id:bytes,version:u256)->DynArray[str]:
        return self._version_value(mandate_id,version,self.ad)
    @gl.public.view
    def get_authority_rule_hashes(self,mandate_id:bytes,version:u256)->DynArray[bytes]:
        return self._version_value(mandate_id,version,self.ae)
    @gl.public.view
    def get_human_mode(self,mandate_id:bytes,version:u256)->u256:
        return self._version_value(mandate_id,version,self.af)
    @gl.public.view
    def get_human_approver(self,mandate_id:bytes,version:u256)->str:
        return str(self._version_value(mandate_id,version,self.ag))
