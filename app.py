import streamlit as st
import random
import copy
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import math

# --- 0. Enum(열거형) 정의 ---
class TaxType(str, Enum): 
    CORP = "법인세"
    VAT = "부가세"
    COMMON = "공통"

class AttackCategory(str, Enum): 
    COST = "비용"
    REVENUE = "수익"
    CAPITAL = "자본"
    COMMON = "공통"

class MethodType(str, Enum): 
    INTENTIONAL = "고의적 누락"
    ERROR = "단순 오류"
    CAPITAL_TX = "자본 거래"

class DifficultyTier(str, Enum):
    EASY = "중소기업"
    MEDIUM = "중견기업"
    HARD = "대기업"
    EXPERT = "글로벌기업"

# --- 헬퍼 함수 ---
def format_krw(amount):
    """금액을 한국 원화 형식으로 포맷팅"""
    if amount is None: 
        return "N/A"
    try:
        if abs(amount) >= 1_000_000: 
            return f"{amount / 1_000_000:,.1f}조원"
        elif abs(amount) >= 10_000: 
            return f"{amount / 10_000:,.0f}억원"
        elif abs(amount) >= 100: 
            return f"{amount / 100:,.0f}억원"
        else: 
            return f"{amount:,.0f}백만원"
    except Exception: 
        return f"{amount} (Format Error)"

def get_enum_values(enum_or_list):
    """Enum이나 Enum 리스트를 값 리스트로 변환"""
    if isinstance(enum_or_list, list):
        return [e.value for e in enum_or_list if hasattr(e, 'value')]
    elif hasattr(enum_or_list, 'value'):
        return [enum_or_list.value]
    return []

def safe_get_enum_value(enum_obj, default="N/A"):
    """안전하게 Enum 값 가져오기"""
    try:
        if hasattr(enum_obj, 'value'):
            return enum_obj.value
        return default
    except:
        return default

# --- 1. 데이터 클래스 정의 ---
@dataclass
class Card:
    name: str
    description: str
    cost: int

@dataclass
class TaxManCard(Card):
    hp: int
    max_hp: int
    focus: int
    analysis: int
    persuasion: int
    evidence: int
    data: int
    ability_name: str
    ability_desc: str
    
    def __init__(self, name, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        nerfed_hp = int(hp * 0.8)
        super().__init__(name, description, cost)
        self.hp = nerfed_hp
        self.max_hp = nerfed_hp
        self.focus = focus
        self.analysis = analysis
        self.persuasion = persuasion
        self.evidence = evidence
        self.data = data
        self.ability_name = ability_name
        self.ability_desc = ability_desc

@dataclass
class LogicCard(Card):
    base_damage: int
    tax_type: List[TaxType]
    attack_category: List[AttackCategory]
    text: str
    special_effect: Optional[Dict[str, Any]] = None
    special_bonus: Optional[Dict[str, Any]] = None
    just_created: bool = False
    
    def __post_init__(self):
        # 비용 증가를 생성 시점에 처리
        self.cost = max(0, self.cost + 1)

@dataclass
class EvasionTactic:
    name: str
    description: str
    total_amount: int
    tax_type: Any  # TaxType | list[TaxType]
    method_type: MethodType
    tactic_category: AttackCategory
    exposed_amount: int = 0
    is_cleared: bool = False

class ResidualTactic(EvasionTactic):
    def __init__(self, remaining_tax):
        super().__init__(
            name="[잔여 혐의 조사]",
            description=f"특정 혐의를 모두 적발했습니다. 남은 목표 세액 {remaining_tax:,}억원을 마저 추징합니다.",
            total_amount=remaining_tax,
            tax_type=[TaxType.COMMON],
            method_type=MethodType.ERROR,
            tactic_category=AttackCategory.COMMON
        )
    
    @property
    def is_cleared(self): 
        return False
    
    @is_cleared.setter
    def is_cleared(self, value): 
        pass

@dataclass
class Company:
    name: str
    size: str
    description: str
    real_case_desc: str
    revenue: int
    operating_income: int
    tax_target: int
    team_hp_damage: tuple
    tactics: List[EvasionTactic]
    defense_actions: List[str]
    difficulty_tier: DifficultyTier
    current_collected_tax: int = 0
    
    def __post_init__(self):
        # 난이도별 데미지 조정
        min_dmg, max_dmg = self.team_hp_damage
        
        if self.difficulty_tier == DifficultyTier.EASY:
            multiplier = 0.7
        elif self.difficulty_tier == DifficultyTier.MEDIUM:
            multiplier = 0.9
        elif self.difficulty_tier == DifficultyTier.HARD:
            multiplier = 1.1
        else:  # EXPERT
            multiplier = 1.3
        
        self.team_hp_damage = (
            math.ceil(min_dmg * multiplier),
            math.ceil(max_dmg * multiplier)
        )

@dataclass
class Artifact:
    name: str
    description: str
    effect: Dict[str, Any]

# --- 대미지 계산 클래스 ---
class DamageCalculator:
    """대미지 계산을 담당하는 클래스"""
    
    def __init__(self, card, tactic, company, team_members, team_stats, stage_level):
        self.card = card
        self.tactic = tactic
        self.company = company
        self.team_members = team_members
        self.team_stats = team_stats
        self.stage_level = stage_level
        self.log_messages = []
        
    def calculate(self, penalty_mult=1.0):
        """모든 대미지 계산을 수행하고 결과 반환"""
        result = {
            'base_damage': self.card.base_damage,
            'stage_bonus': 0,
            'team_bonus': 0,
            'ability_bonus': 0,
            'multiplier': 1.0,
            'multiplier_desc': [],
            'final_damage': 0,
            'logs': []
        }
        
        # 1. 기본 대미지 + 스테이지 보너스
        base_with_stage = self._calculate_base_and_stage_bonus()
        result['stage_bonus'] = base_with_stage - self.card.base_damage
        
        # 2. 규모 보정
        scaled_damage = self._apply_scale_correction(base_with_stage)
        
        # 3. 팀 스탯 보너스
        team_bonus = self._calculate_team_bonus()
        result['team_bonus'] = team_bonus
        
        # 4. 캐릭터 어빌리티 보너스
        ability_bonus = self._calculate_ability_bonus()
        result['ability_bonus'] = ability_bonus
        
        total_damage = scaled_damage + team_bonus + ability_bonus
        
        # 5. 승수 계산
        multiplier, mult_desc = self._calculate_multipliers()
        result['multiplier'] = multiplier * penalty_mult
        result['multiplier_desc'] = mult_desc
        
        # 최종 대미지
        result['final_damage'] = int(total_damage * result['multiplier'])
        result['logs'] = self.log_messages
        
        return result
    
    def _calculate_base_and_stage_bonus(self):
        """기본 대미지 + 스테이지 숙련 보너스"""
        base = self.card.base_damage
        basic_cards = ["단순 자료 대사", "기본 경비 적정성 검토", 
                      "단순 경비 처리 오류 지적", "세금계산서 대사"]
        
        if self.card.name in basic_cards:
            if self.stage_level == 3: 
                bonus = 50
            elif self.stage_level == 2: 
                bonus = 30
            elif self.stage_level == 1: 
                bonus = 15
            else:
                bonus = 0
            
            if bonus > 0:
                self.log_messages.append(f"📈 [숙련도] +{bonus}억원")
            return base + bonus
        
        return base
    
    def _apply_scale_correction(self, damage):
        """기업 규모에 따른 보정"""
        ref = 500
        scale = (self.company.tax_target / ref) ** 0.5 if self.company.tax_target > 0 else 0.5
        capped = max(0.5, min(2.0, scale))
        
        if abs(capped - 1.0) > 0.01:
            scaled = int(damage * capped)
            self.log_messages.append(f"⚖️ [규모 보정] {damage}→{scaled}억원")
            return scaled
        
        return damage
    
    def _calculate_team_bonus(self):
        """팀 스탯 보너스 계산"""
        bonus = 0
        stats = self.team_stats
        
        if any(c in [AttackCategory.COST, AttackCategory.COMMON] for c in self.card.attack_category):
            analysis_bonus = int(stats["analysis"] * 0.5)
            if analysis_bonus > 0:
                bonus += analysis_bonus
                self.log_messages.append(f"🧠 [분석력] +{analysis_bonus}억원")
        
        if AttackCategory.CAPITAL in self.card.attack_category:
            data_bonus = int(stats["data"] * 1.0)
            if data_bonus > 0:
                bonus += data_bonus
                self.log_messages.append(f"💾 [데이터] +{data_bonus}억원")
        
        if '판례' in self.card.name:
            persuasion_bonus = int(stats["persuasion"] * 1.0)
            if persuasion_bonus > 0:
                bonus += persuasion_bonus
                self.log_messages.append(f"💬 [설득력] +{persuasion_bonus}억원")
        
        if '압수' in self.card.name:
            evidence_bonus = int(stats["evidence"] * 1.5)
            if evidence_bonus > 0:
                bonus += evidence_bonus
                self.log_messages.append(f"📂 [증거력] +{evidence_bonus}억원")
        
        return bonus
    
    def _calculate_ability_bonus(self):
        """캐릭터 특수 능력 보너스"""
        bonus = 0
        member_names = [m.name for m in self.team_members]
        
        if "이찰수" in member_names and self.card.name in ["기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]:
            bonus += 8
            self.log_messages.append("✨ [기본기] +8억원")
        
        if "임향수" in member_names and ('분석' in self.card.name or '자료' in self.card.name or '추적' in self.card.name or AttackCategory.CAPITAL in self.card.attack_category):
            ability_bonus = int(self.team_stats["analysis"] * 0.1 + self.team_stats["data"] * 0.1)
            if ability_bonus > 0:
                bonus += ability_bonus
                self.log_messages.append(f"✨ [기획 조사] +{ability_bonus}억원")
        
        if "유재전" in member_names and self.tactic.method_type == MethodType.ERROR:
            ability_bonus = int(self.team_stats["persuasion"] / 10)
            if ability_bonus > 0:
                bonus += ability_bonus
                self.log_messages.append(f"✨ [정기 조사] +{ability_bonus}억원")
        
        if "김태후" in member_names and AttackCategory.CAPITAL in self.card.attack_category:
            ability_bonus = int(self.team_stats["evidence"] * 0.1)
            if ability_bonus > 0:
                bonus += ability_bonus
                self.log_messages.append(f"✨ [심층 기획] +{ability_bonus}억원")
        
        return bonus
    
    def _calculate_multipliers(self):
        """각종 승수 계산"""
        mult = 1.0
        descriptions = []
        
        # 카드 자체 보너스
        if self.card.special_bonus and self.card.special_bonus.get('target_method') == self.tactic.method_type:
            card_mult = self.card.special_bonus.get('multiplier', 1.0)
            mult *= card_mult
            descriptions.append(f"🔥 [{self.card.special_bonus.get('bonus_desc')}]")
            
            # 조용규 특수 능력
            member_names = [m.name for m in self.team_members]
            if "조용규" in member_names and self.card.name == "판례 제시":
                mult *= 2
                descriptions.append("✨ [세법 교본 x2]")
        
        # 캐릭터 특수 승수
        member_names = [m.name for m in self.team_members]
        
        if "한중후" in member_names:
            if self.company.size in ["외국계", "글로벌 기업"] or self.tactic.method_type == MethodType.CAPITAL_TX:
                mult *= 1.3
                descriptions.append("✨ [역외탈세 +30%]")
        
        if "서영택" in member_names:
            if self.company.size in ["대기업", "외국계", "글로벌 기업"] and TaxType.CORP in self.card.tax_type:
                mult *= 1.25
                descriptions.append("✨ [대기업 저격 +25%]")
        
        if "이현동" in member_names and self.tactic.method_type == MethodType.INTENTIONAL:
            mult *= 1.2
            descriptions.append("✨ [지하경제 양성화 +20%]")
        
        return mult, descriptions

# --- 게임 상태 관리 클래스 ---
class GameState:
    """게임 상태를 관리하는 클래스"""
    
    @staticmethod
    def initialize():
        """게임 상태 초기화"""
        defaults = {
            'game_state': 'MAIN_MENU',
            'player_team': [],
            'player_deck': [],
            'player_hand': [],
            'player_discard': [],
            'player_artifacts': [],
            'team_hp': 0,
            'team_max_hp': 0,
            'player_focus_current': 0,
            'player_focus_max': 0,
            'team_stats': {'analysis': 0, 'persuasion': 0, 'evidence': 0, 'data': 0},
            'company_order': [],
            'current_battle_company': None,
            'current_stage_level': 0,
            'total_collected_tax': 0,
            'battle_log': [],
            'selected_card_index': None,
            'bonus_draw': 0,
            'battle_stats': {
                'turns_taken': 0,
                'cards_played': 0,
                'total_damage_dealt': 0,
                'tactics_cleared': 0
            },
            'show_tutorial': True
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def reset_battle_state():
        """전투 관련 상태만 초기화"""
        battle_keys = [
            'selected_card_index', 'bonus_draw', 'turn_first_card_played',
            'kim_dj_effect_used', 'cost_reduction_active', 
            'cost_reduction_active_just_used', 'hit_effect_company',
            'hit_effect_player'
        ]
        for key in battle_keys:
            if key in st.session_state:
                del st.session_state[key]

# --- 교육 시스템 ---
class EducationalSystem:
    """교육적 피드백과 팁을 제공하는 시스템"""
    
    GLOSSARY = {
        "부당행위계산부인": "특수관계자 간 거래에서 시가와 다른 가격으로 거래하여 부당하게 이익을 이전한 경우, 정상가격으로 재계산하여 과세하는 제도",
        "조세피난처": "법인세율이 매우 낮거나 없으며, 금융 정보 공개를 거부하는 국가나 지역. 역외탈세의 주요 수단으로 활용됨",
        "이전가격": "특수관계에 있는 기업 간 거래 가격. 이를 조작하여 소득을 저세율 국가로 이전할 수 있음",
        "고정사업장(PE)": "외국 기업이 국내에서 사업을 영위하는 고정된 장소. 고정사업장이 인정되면 국내 법인세 과세 대상",
        "가공경비": "실제 지출이 없거나 실체가 없는 거래에 대해 허위로 계상한 비용",
        "차명계좌": "타인의 명의를 빌려 개설한 계좌. 자금 흐름을 숨기고 탈세하는데 악용됨",
        "손금불산입": "회계상 비용으로 계상되었으나 세법상 비용으로 인정되지 않는 항목. 법인세 계산 시 소득에 가산됨",
        "자료상": "실물 거래 없이 세금계산서만 거래하여 부당한 세액공제를 도와주고 수수료를 받는 불법 업체",
        "정상가격(ALP)": "특수관계가 없는 독립된 기업 간 거래에서 적용될 가격. 이전가격 세제의 핵심 개념"
    }
    
    @staticmethod
    def get_attack_tip(card, tactic, multiplier):
        """공격 시 교육적 팁 제공"""
        tips = []
        
        # 완벽한 매칭
        if multiplier >= 2.0:
            tips.append("💡 [조사 팁] 혐의 유형과 완벽하게 일치하는 카드로 최대 효과를 냈습니다!")
        
        # 메소드별 팁
        if tactic.method_type == MethodType.INTENTIONAL and '압수' in card.name:
            tips.append("💡 [조사 팁] 고의적 누락은 현장 증거 확보가 핵심입니다.")
        elif tactic.method_type == MethodType.ERROR and '판례' in card.name:
            tips.append("💡 [조사 팁] 단순 오류는 법령과 판례로 설득하는 것이 효과적입니다.")
        elif tactic.method_type == MethodType.CAPITAL_TX and '자본' in card.name:
            tips.append("💡 [조사 팁] 자본거래는 복잡한 자금 흐름 추적이 필요합니다.")
        
        return tips
    
    @staticmethod
    def generate_battle_report(company, battle_stats):
        """전투 종료 후 상세 보고서 생성"""
        report = {
            'efficiency': {
                'damage_per_turn': battle_stats['total_damage_dealt'] / max(battle_stats['turns_taken'], 1),
                'cards_per_turn': battle_stats['cards_played'] / max(battle_stats['turns_taken'], 1),
                'target_achievement': (company.current_collected_tax / company.tax_target * 100) if company.tax_target > 0 else 0
            },
            'suggestions': []
        }
        
        # 개선 제안 생성
        if report['efficiency']['damage_per_turn'] < 50:
            report['suggestions'].append("⚠️ 턴당 추징액이 낮습니다. 팀 스탯을 활용할 수 있는 카드를 더 사용해보세요.")
        
        if report['efficiency']['cards_per_turn'] < 2:
            report['suggestions'].append("💡 집중력을 효율적으로 사용하지 못했습니다. 저비용 카드와 드로우 카드를 활용하세요.")
        
        if battle_stats['tactics_cleared'] < len(company.tactics):
            report['suggestions'].append("📋 일부 혐의를 완전히 적발하지 못했습니다. 혐의별로 특화된 카드를 사용하면 더 효과적입니다.")
        
        return report

# --- 2. 게임 데이터베이스 (DB) ---
TAX_MAN_DB = {
    "lim": TaxManCard(name="임향수", description="조사통의 대부. 대기업 비자금, 불법 증여 조사 지휘 경험 풍부.", cost=0, hp=120, focus=3, analysis=10, persuasion=10, evidence=10, data=10, ability_name="[기획 조사]", ability_desc="매 턴 집중력+1. 분석/데이터 스탯 비례 비용/자본 카드 피해량 증가."),
    "han": TaxManCard(name="한중후", description="국제조세 글로벌기업. OECD 파견 경험으로 국제 공조 및 BEPS 이해 깊음.", cost=0, hp=80, focus=2, analysis=9, persuasion=6, evidence=8, data=9, ability_name="[역외탈세 추적]", ability_desc="'외국계' 기업 또는 '자본 거래' 혐의 공격 시 최종 피해량 +30%."),
    "baek": TaxManCard(name="백용호", description="세제 글로벌기업. TIS, NTIS 등 과학세정 인프라 구축 경험.", cost=0, hp=90, focus=2, analysis=7, persuasion=10, evidence=9, data=7, ability_name="[TIS 분석]", ability_desc="'금융거래 분석', '빅데이터 분석' 등 데이터 관련 카드 비용 -1."),
    "seo": TaxManCard(name="서영택", description="조사 글로벌기업. 변칙 상속/증여 조사를 강력 지휘. 대기업 조사 정통.", cost=0, hp=100, focus=2, analysis=8, persuasion=9, evidence=8, data=7, ability_name="[대기업 저격]", ability_desc="'대기업', '외국계' 기업의 '법인세' 혐의 카드 공격 시 최종 피해량 +25%."),
    "kim_dj": TaxManCard(name="김대조", description="세정 운영 글로벌기업. 데이터 기반 대규모 조사 경험.", cost=0, hp=90, focus=2, analysis=10, persuasion=7, evidence=7, data=10, ability_name="[부동산 투기 조사]", ability_desc="팀 '데이터' 스탯 50+ 시, 턴 시작 시 '금융거래 분석' 카드 1장 생성."),
    "lee_hd": TaxManCard(name="이현동", description="강력한 추진력의 조사통. 지하경제 양성화 및 역외탈세 추적 의지 강함.", cost=0, hp=100, focus=3, analysis=7, persuasion=8, evidence=10, data=8, ability_name="[지하경제 양성화]", ability_desc="'고의적 누락(Intentional)' 혐의 공격의 최종 피해량 +20%."),
    "kim": TaxManCard(name="김철주", description="현장 글로벌기업. 서울청 조사0국 '지하경제 양성화' 관련 조사 다수 수행.", cost=0, hp=110, focus=2, analysis=6, persuasion=8, evidence=9, data=5, ability_name="[압수수색]", ability_desc="'현장 압수수색' 카드 사용 시 15% 확률로 '결정적 증거' 추가 획득."),
    "oh": TaxManCard(name="전팔성", description="[가상] 데이터 글로벌기업. TIS 초기 멤버로 시스템 이해도 높음. 신종 거래 분석 능함.", cost=0, hp=110, focus=2, analysis=7, persuasion=6, evidence=7, data=8, ability_name="[데이터 마이닝]", ability_desc="기본 적출액 70억 이상 '데이터' 관련 카드(자금출처조사 등) 피해량 +15."),
    "jo": TaxManCard(name="조용규", description="세법 이론가. 교육원 교수 경험. 법리 해석과 판례 분석 뛰어남.", cost=0, hp=80, focus=3, analysis=9, persuasion=7, evidence=6, data=7, ability_name="[세법 교본]", ability_desc="'판례 제시', '법령 재검토' 카드의 효과(피해량/드로우) 2배 적용."),
    "park": TaxManCard(name="박조연", description="[가상] 세법 신동. 세무사/CPA 동시 합격 특채. 날카로운 법리 검토 능력.", cost=0, hp=70, focus=3, analysis=7, persuasion=5, evidence=6, data=7, ability_name="[법리 검토]", ability_desc="턴마다 처음 사용하는 '분석' 또는 '설득' 유형 카드의 비용 -1."),
    "lee": TaxManCard(name="이찰수", description="[가상] 7급 공채 신입. 열정 넘치나 경험 부족. 기본기 충실.", cost=0, hp=80, focus=2, analysis=5, persuasion=5, evidence=5, data=5, ability_name="[기본기]", ability_desc="'기본 경비 적정성 검토', '단순 경비 처리 오류 지적' 카드 피해량 +8."),
    "ahn_wg": TaxManCard(name="안원규", description="특수 조사의 귀재. 서울청 조사0국 등에서 대기업 비자금 등 특수 조사 경험 풍부.", cost=0, hp=110, focus=2, analysis=8, persuasion=5, evidence=10, data=6, ability_name="[특수 조사]", ability_desc="'현장 압수수색', '차명계좌 추적' 카드 비용 -1 (최소 0)."),
    "yoo_jj": TaxManCard(name="유재전", description="관리자. 서울청 조사0국 대기업 정기 조사 및 상속/증여세 조사 담당. 분석/설득 강점.", cost=0, hp=100, focus=2, analysis=8, persuasion=7, evidence=7, data=7, ability_name="[정기 조사 전문]", ability_desc="'단순 오류(Error)' 혐의 공격 시, 팀 '설득' 스탯 10당 피해량 +1."),
    "kim_th": TaxManCard(name="김태후", description="관리자. 중부청 조사0국 대기업/중견기업 심층 기획 및 국제거래 조사 담당. 증거 확보/데이터 분석 탁월.", cost=0, hp=105, focus=2, analysis=9, persuasion=5, evidence=9, data=8, ability_name="[심층 기획 조사]", ability_desc="'자본 거래(Capital Tx)' 혐의 공격 시, 팀 '증거' 스탯의 10%만큼 추가 피해."),
    "jeon_j": TaxManCard(name="전준", description="실무 과장. 중부청 조사0국. 조사 현장 지휘 경험 풍부, 팀원 능력 활용 능숙.", cost=0, hp=85, focus=3, analysis=7, persuasion=6, evidence=6, data=6, ability_name="[실무 지휘]", ability_desc="턴 시작 시, **팀**의 다음 카드 사용 비용 -1.")
}

LOGIC_CARD_DB = {
    "c_tier_01": LogicCard(name="단순 자료 대사", cost=0, base_damage=4, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="매입/매출 자료 단순 비교.", text="자료 대사 기본 습득."),
    "c_tier_02": LogicCard(name="법령 재검토", cost=0, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 1장 뽑기.", text="관련 법령 재검토.", special_effect={"type": "draw", "value": 1}),
    "util_01": LogicCard(name="초과근무", cost=1, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 2장 뽑기.", text="밤샘 근무로 단서 발견!", special_effect={"type": "draw", "value": 2}),
    "basic_01": LogicCard(name="기본 경비 적정성 검토", cost=1, base_damage=8, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST, AttackCategory.COMMON], description="기본 비용 처리 적정성 검토.", text="법인세법 비용 조항 분석."),
    "basic_02": LogicCard(name="단순 경비 처리 오류 지적", cost=1, base_damage=10, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST, AttackCategory.COMMON], description="증빙 미비 경비 지적.", text="증빙 대조 기본 습득."),
    "b_tier_04": LogicCard(name="세금계산서 대사", cost=1, base_damage=12, tax_type=[TaxType.VAT], attack_category=[AttackCategory.REVENUE, AttackCategory.COST], description="매입/매출 세금계산서 합계표 대조.", text="합계표 불일치 확인."),
    "c_tier_03": LogicCard(name="가공 증빙 수취 분석", cost=2, base_damage=15, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.COST, AttackCategory.REVENUE], description="실물 거래 없이 세금계산서만 수취한 정황을 분석합니다.", text="가짜 세금계산서 흐름 파악."),
    "corp_01": LogicCard(name="접대비 한도 초과", cost=2, base_damage=25, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="법정 한도를 초과한 접대비를 비용으로 처리한 부분을 지적합니다.", text="법인세법 접대비 조항 습득."),
    "b_tier_03": LogicCard(name="판례 제시", cost=2, base_damage=22, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="유사한 탈루 또는 오류 사례에 대한 과거 판례를 제시하여 설득합니다.", text="대법원 판례 제시.", special_bonus={'target_method': MethodType.ERROR, 'multiplier': 2.0, 'bonus_desc': '단순 오류에 2배 피해'}),
    "b_tier_05": LogicCard(name="인건비 허위 계상", cost=2, base_damage=30, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST, AttackCategory.CAPITAL], description="실제 근무하지 않는 친인척 등에게 급여를 지급한 것처럼 꾸며 비용 처리한 것을 적발합니다.", text="급여대장-근무 내역 불일치 확인."),
    "util_02": LogicCard(name="빅데이터 분석", cost=2, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="적 혐의 유형과 일치하는 카드 1장 서치.", text="TIS 빅데이터 패턴 발견!", special_effect={"type": "search_draw", "value": 1}),
    "corp_02": LogicCard(name="업무 무관 자산 비용 처리", cost=3, base_damage=35, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST, AttackCategory.CAPITAL], description="대표이사 개인 차량 유지비, 가족 해외여행 경비 등 업무와 관련 없는 비용을 법인 비용으로 처리한 것을 적발합니다.", text="벤츠 운행일지 확보!", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 1.5, 'bonus_desc': '고의적 누락에 1.5배 피해'}),
    "cap_01": LogicCard(name="부당행위계산부인", cost=3, base_damage=40, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL, AttackCategory.REVENUE], description="특수관계자와의 거래(자산 고가 매입, 저가 양도 등)에서 시가를 조작하여 이익을 분여한 혐의를 지적합니다.", text="계열사 간 저가 양수도 적발.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
    "b_tier_01": LogicCard(name="금융거래 분석", cost=3, base_damage=45, tax_type=[TaxType.CORP], attack_category=[AttackCategory.REVENUE, AttackCategory.CAPITAL], description="의심스러운 자금 흐름을 추적하여 숨겨진 수입이나 부당한 자본 거래를 포착합니다.", text="FIU 분석 기법 습득."),
    "b_tier_02": LogicCard(name="현장 압수수색", cost=3, base_damage=25, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="조사 현장을 방문하여 장부와 실제 재고, 자산 등을 대조하고 숨겨진 자료를 확보합니다.", text="재고 불일치 확인.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "a_tier_02": LogicCard(name="차명계좌 추적", cost=3, base_damage=50, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.REVENUE, AttackCategory.CAPITAL], description="타인 명의로 개설된 계좌를 통해 수입 금액을 은닉한 정황을 포착하고 자금 흐름을 추적합니다.", text="차명계좌 흐름 파악.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "cap_02": LogicCard(name="불공정 자본거래", cost=4, base_damage=80, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="합병, 증자, 감자 등 과정에서 불공정한 비율을 적용하여 주주(총수 일가)에게 이익을 증여한 혐의를 조사합니다.", text="상증세법상 이익의 증여.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "a_tier_01": LogicCard(name="자금출처조사", cost=4, base_damage=90, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL, AttackCategory.REVENUE], description="고액 자산가의 자산 형성 과정에서 불분명한 자금의 출처를 소명하도록 요구하고, 탈루 혐의를 조사합니다.", text="수십 개 차명계좌 흐름 파악."),
    "s_tier_01": LogicCard(name="국제거래 과세논리", cost=4, base_damage=65, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL, AttackCategory.REVENUE, AttackCategory.COST], description="이전가격 조작, 고정사업장 회피 등 국제거래를 이용한 조세회피 전략을 분석하고 과세 논리를 개발합니다.", text="BEPS 보고서 이해.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "s_tier_02": LogicCard(name="조세피난처 역외탈세", cost=5, base_damage=130, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL, AttackCategory.REVENUE], description="조세피난처에 설립된 특수목적회사(SPC) 등을 이용하여 해외 소득을 은닉한 역외탈세 혐의를 조사합니다.", text="BVI, 케이맨 SPC 실체 규명.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
    "vat_01": LogicCard(name="위장가맹점 추적", cost=2, base_damage=20, tax_type=[TaxType.VAT, TaxType.CORP], attack_category=[AttackCategory.REVENUE], description="신용카드 결제 내역을 분석하여, 타 업종으로 위장한 가맹점을 통한 매출 누락을 적발합니다.", text="PG사 자료 확보.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 1.5, 'bonus_desc': '고의적 누락에 1.5배 피해'}),
    "err_01": LogicCard(name="세무조정 오류 시정", cost=2, base_damage=25, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="기업의 세무조정계산서를 검토하여, 감가상각, 충당금 설정 등에서 발생한 명백한 회계/세법 적용 오류를 지적합니다.", text="조정계산서 검토.", special_bonus={'target_method': MethodType.ERROR, 'multiplier': 2.0, 'bonus_desc': '단순 오류에 2배 피해'}),
    "vat_02": LogicCard(name="매입세액 부당공제", cost=2, base_damage=28, tax_type=[TaxType.VAT], attack_category=[AttackCategory.COST, AttackCategory.COMMON], description="사업과 관련 없는 매입(예: 대표 개인 골프장 비용)에 대한 세금계산서를 받아 매입세액을 부당하게 공제/환급받은 것을 적발합니다.", text="사적 경비 부인.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 1.5, 'bonus_desc': '고의적 누락에 1.5배 피해'}),
}

ARTIFACT_DB = {
    "coffee": Artifact(name="☕ 믹스 커피", description="턴 시작 시 집중력 +1.", effect={"type": "on_turn_start", "value": 1, "subtype": "focus"}),
    "forensic": Artifact(name="💻 포렌식 장비", description="팀 '증거(Evidence)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_evidence"}),
    "plan": Artifact(name="📜 조사계획서", description="첫 턴 카드 +1장.", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
    "recorder": Artifact(name="🎤 녹음기", description="팀 '설득(Persuasion)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_persuasion"}),
    "book": Artifact(name="📖 오래된 법전", description="'판례 제시', '법령 재검토' 비용 -1.", effect={"type": "on_cost_calculate", "value": -1, "target_cards": ["판례 제시", "법령 재검토"]}),
    "report": Artifact(name="📊 분기 보고서", description="팀 '분석(Analysis)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_analysis"}),
    "badge": Artifact(name="🎖️ 우수 조사관 배지", description="첫 턴 카드 +1장. (조사계획서와 중첩 가능)", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
}

COMPANY_DB = [
    # --- C Group (Easy) ---
    Company(
        name="(주)가나푸드", size="소규모", revenue=8000, operating_income=800, tax_target=10, team_hp_damage=(5, 12),
        description="인기 **SNS 인플루언서**가 운영하는 **온라인 쇼핑몰**(식품 유통). 대표는 **고가 외제차**, **명품** 과시.",
        real_case_desc="""[교육] 최근 **온라인 플랫폼 기반 사업자**들의 탈세가 증가하고 있습니다. 주요 유형은 다음과 같습니다:
* **개인 계좌** 사용: 법인 계좌 대신 대표 또는 가족 명의 계좌로 **매출 대금**을 받아 **매출 누락**.
* **업무 무관 경비**: 법인 명의 **슈퍼카 리스료**, 대표 개인 **명품 구매 비용**, **가족 해외여행 경비** 등을 법인 비용으로 처리 (**손금 불산입** 및 대표 **상여** 처분 대상).
* **증빙 미비**: 실제 지출 없이 **가공 경비** 계상 후 증빙 미비.""",
        tactics=[
            EvasionTactic("사주 개인 유용 및 경비", "대표 개인 **명품 구매**(5천만원), **해외여행 경비**(3천만원), **자녀 학원비**(2천만원) 등 총 **1억원**을 법인 비용 처리.", 7, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST),
            EvasionTactic("매출 누락 (개인 계좌)", "고객으로부터 받은 **현금 매출** 및 **계좌 이체** 대금 중 **3억원**을 대표 개인 계좌로 받아 **매출 신고 누락**.", 3, [TaxType.CORP, TaxType.VAT], MethodType.INTENTIONAL, AttackCategory.REVENUE)
        ],
        defense_actions=["담당 세무사가 '실수' 주장.", "대표가 '개인 돈 썼다'고 항변.", "경리 직원이 '몰랐다' 시전."],
        difficulty_tier=DifficultyTier.EASY
    ),
    Company(
        name="㈜코팡 (Kopang)", size="중견기업", revenue=300000, operating_income=10000, tax_target=50, team_hp_damage=(10, 20),
        description="빠른 배송으로 유명한 **E-커머스 플랫폼**. **쿠폰 발행**, **포인트 적립** 등 프로모션 비용이 막대함.",
        real_case_desc="""[교육] **E-커머스 플랫폼**은 **고객 유치 비용**(쿠폰, 적립금)의 회계 처리가 쟁점입니다.
* **할인 vs 비용**: 고객에게 지급하는 **쿠폰/포인트**를 **매출 할인**(매출 차감)으로 볼지, **판매 촉진비**(비용)으로 볼지에 따라 과세 소득이 달라집니다.
* **시점**: 해당 비용을 **발생 시점**에 인식할지, **사용 시점**에 인식할지에 대한 **회계 처리 오류**가 빈번히 발생합니다.
* **부가세**: **제3자**가 부담하는 쿠폰 비용, **마일리지** 결제 부분 등 복잡한 **부가세 과세표준** 산정 오류가 발생하기 쉽습니다.""",
        tactics=[
            EvasionTactic("포인트 비용 인식 오류", "고객에게 **적립**해준 **포인트/마일리지** 전액(50억원)을 **발생 시점**에 **비용** 처리. 실제 **사용 시점** 기준으로 재계산 필요.", 20, TaxType.CORP, MethodType.ERROR, AttackCategory.COST),
            EvasionTactic("쿠폰 부가세 과표 오류", "제휴사 부담 **할인 쿠폰** 금액(30억원)을 **부가세 과세표준**에서 임의로 제외하여 **부가세** 신고 누락.", 30, TaxType.VAT, MethodType.ERROR, AttackCategory.REVENUE)
        ],
        defense_actions=["'일관된 회계 기준' 적용했다고 주장.", "업계 관행이라며 소극적 대응.", "방대한 거래 데이터 제출, 검토 지연 유도."],
        difficulty_tier=DifficultyTier.EASY
    ),
    Company(
        name="㈜넥선 (Nexun)", size="중견기업", revenue=200000, operating_income=15000, tax_target=100, team_hp_damage=(15, 30),
        description="최근 급성장한 **게임/IT 기업**. **R&D 투자**가 많고 임직원 **스톡옵션** 부여가 잦습니다.",
        real_case_desc="""[교육] IT 기업은 **연구개발(R&D) 세액공제** 적용 요건이 까다롭고 변경이 잦아 오류가 발생하기 쉽습니다. 특히 **인건비**나 **위탁개발비**의 적격 여부가 주된 쟁점입니다. 또한, 임직원에게 부여한 **스톡옵션**의 경우, 행사 시점의 **시가 평가** 및 과세 방식(근로소득 vs 기타소득)에 대한 검토가 필요하며, 이를 이용한 **세금 회피** 시도가 있을 수 있습니다.""",
        tactics=[
            EvasionTactic("R&D 비용 부당 공제", "**연구개발 활동**과 직접 관련 없는 **인건비** 및 **일반 관리비** 50억원을 **R&D 세액공제** 대상 비용으로 허위 계상.", 60, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST),
            EvasionTactic("스톡옵션 시가 저가 평가", "임원에게 부여한 **스톡옵션** 행사 시 **비상장주식 가치**를 의도적으로 낮게 평가하여 **소득세(근로소득)** 40억원 탈루.", 40, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL)
        ],
        defense_actions=["회계법인이 '적격 R&D' 의견 제시.", "연구 노트 등 서류 미비.", "스톡옵션 평가는 '정관 규정' 따랐다고 주장."],
        difficulty_tier=DifficultyTier.EASY
    ),
    # --- B Group (Medium) ---
    Company(
        name="(주)한늠석유 (자료상)", size="중견기업", revenue=70000, operating_income=-800, tax_target=150, team_hp_damage=(20, 35),
        description="전형적인 '**자료상**' 의심 업체. **유가보조금 부정수급** 및 **허위 세금계산서** 발행 전력.",
        real_case_desc="""[교육] **자료상**은 실제 거래 없이 세금계산서만 사고파는 행위를 통해 국가 재정을 축내는 대표적인 **조세 범죄**입니다. 실물 거래 없이 **가공 세금계산서**를 발행하여 타 기업의 **비용**을 부풀려주거나(매입 자료상), **매출**을 대신 받아주어(매출 자료상) 부가가치세와 법인세를 탈루하도록 돕고 수수료를 챙깁니다.""",
        tactics=[
            EvasionTactic("유가보조금 부정수급 공모", "**화물차주**들과 짜고 **허위 세금계산서**(월 10억원) 발행, 실제 주유 없이 **유가보조금** 총 100억원 편취.", 100, [TaxType.VAT, TaxType.COMMON], MethodType.INTENTIONAL, AttackCategory.REVENUE),
            EvasionTactic("자료상 행위 (중개)", "실물 거래 없이 **폭탄업체**로부터 **가짜 세금계산서**(50억원)를 매입하여 다른 법인에 수수료 받고 판매.", 50, TaxType.VAT, MethodType.INTENTIONAL, AttackCategory.COST)
        ],
        defense_actions=["대표 해외 도피 시도.", "사무실 잠적 (페이퍼컴퍼니).", "관련 장부 소각 및 증거 인멸 시도."],
        difficulty_tier=DifficultyTier.MEDIUM
    ),
    Company(
        name="(주)대롬건설 (Daelom E&C)", size="중견기업", revenue=500000, operating_income=25000, tax_target=200, team_hp_damage=(20, 30),
        description="다수의 **관급 공사** 수주 이력이 있는 **중견 건설사**. **하도급** 거래가 복잡함.",
        real_case_desc="""[교육] 건설업은 **불투명한 자금 흐름**으로 인해 세무조사 단골 업종 중 하나입니다. 주요 탈루 유형은 다음과 같습니다:
* **원가 허위 계상**: 실제 근무하지 않는 **친인척**이나 **일용직 근로자**의 **인건비**를 허위로 계상하거나, **자재비**를 부풀려 **비자금**을 조성합니다.
* **무자료 거래 및 허위 세금계산서**: **하도급 업체**와 공모하여 실제 용역 제공 없이 **가짜 세금계산서**를 수수하여 비용을 부풀립니다.
* **수입금액 누락**: 공사대금을 **현금**으로 받거나 **차명계좌**로 받아 매출을 누락합니다.
* **진행률 조작**: 아파트/상가 **분양률**을 의도적으로 축소 신고하여, **공사 진행률**에 따른 **수입금액**을 과소 계상합니다.""",
        tactics=[
            EvasionTactic("가공 인건비 계상", "**일용직 근로자** 인건비 150억원을 **허위 계상**하여 비용 처리하고 **비자금** 조성.", 120, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST),
            EvasionTactic("하도급 리베이트", "**하도급 업체** 10여곳에 공사비를 부풀려 지급(80억원)한 뒤, 차액을 **현금 리베이트**로 수수.", 80, [TaxType.CORP, TaxType.VAT], MethodType.INTENTIONAL, AttackCategory.CAPITAL)
        ],
        defense_actions=["현장 소장에게 책임 전가.", "하도급 업체가 영세하여 추적 어려움.", "관련 장부 '화재로 소실' 주장."],
        difficulty_tier=DifficultyTier.MEDIUM
    ),
    Company(
        name="(주)한모약품 (Hanmo Pharm)", size="중견기업", revenue=400000, operating_income=30000, tax_target=300, team_hp_damage=(20, 35),
        description="**신약 개발**에 막대한 자금을 투자하는 **제약/바이오** 기업. **기술 수출** 실적 보유.",
        real_case_desc="""[교육] **제약/바이오** 산업은 **R&D 비용** 및 **무형자산(IP)** 가치 평가가 핵심 쟁점입니다. **R&D 세액공제** 대상이 아닌 비용을 공제받거나, **임상 실패** 가능성이 높은 프로젝트 비용을 **자산(개발비)**으로 과다 계상하여 법인세를 이연/탈루하는 경우가 있습니다. 또한 **조세피난처**의 자회사로 **특허권(IP)**을 **저가 양도**하여 국내 소득을 이전하는 방식도 사용됩니다.""",
        tactics=[
            EvasionTactic("개발비 과다 자산화", "임상 **실패 가능성**이 높은 **신약 파이프라인** 관련 지출 200억원을 **비용**이 아닌 **무형자산(개발비)**으로 처리하여 **법인세** 이연/탈루.", 180, TaxType.CORP, MethodType.ERROR, AttackCategory.COST),
            EvasionTactic("IP 저가 양도", "핵심 **신약 특허권**을 **조세피난처** 소재 **페이퍼컴퍼니** 자회사에 **정상 가격**(150억원)보다 현저히 낮은 30억원에 양도.", 120, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL)
        ],
        defense_actions=["'회계 기준'에 따른 정상적 처리 주장.", "신약 가치 평가는 '미래 불확실성' 반영 필요.", "글로벌 스탠다드라며 자료 제출 비협조."],
        difficulty_tier=DifficultyTier.MEDIUM
    ),
    # --- A Group (Hard) ---
    Company(
        name="(주)로떼 (Lottee)", size="대기업", revenue=30_000_000, operating_income=1_000_000, tax_target=800, team_hp_damage=(18, 30),
        description="**유통, 화학, 건설** 등 다수 계열사 보유 **대기업 그룹**. **순환출자** 구조 및 **경영권 분쟁** 이력.",
        real_case_desc="""[교육] 복잡한 **순환출자** 구조를 가진 대기업은 **그룹사 간 부당 지원** 및 **자본 거래**를 통한 이익 분여가 잦습니다.
* **계열사 간 자금 대여**: **업무 관련성** 없는 **자금 대여** 또는 **저리/무상** 대여를 통해 특정 계열사(주로 총수 일가 지분 높은 곳)를 지원. (**부당행위계산부인** 대상)
* **자산 양수도**: 그룹 내 **자산(부동산, 주식 등)**을 **시가**와 다르게 **저가/고가**로 양수도하여 **법인세** 탈루 및 **이익 증여**.
* **경영권 분쟁**: **형제간 경영권 다툼** 과정에서 **비자금** 조성 또는 **회계 부정** 발생 가능성.""",
        tactics=[
            EvasionTactic("계열사 부당 자금 대여", "**총수 일가** 지분이 높은 **(주)로떼정보**에 **업무 무관** 가지급금 500억원을 **무상**으로 대여.", 500, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL),
            EvasionTactic("부동산 고가 매입", "경영 악화된 **계열사**의 **토지**를 **정상가**(300억)보다 높은 **500억원**에 매입하여 부당 지원.", 300, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL)
        ],
        defense_actions=["'경영 정상화'를 위한 불가피한 지원 주장.", "자산 평가는 '외부 회계법인' 용역 결과.", "경영권 분쟁 관련 자료 제출 거부."],
        difficulty_tier=DifficultyTier.HARD
    ),
    Company(
        name="㈜삼숭물산 (Samsyoong)", size="대기업", revenue=60_000_000, operating_income=2_500_000, tax_target=1200, team_hp_damage=(20, 40),
        description="국내 굴지 **대기업 그룹**의 핵심 계열사. **경영권 승계**, **신사업 투자**, **해외 M&A** 활발.",
        real_case_desc="""[교육] 대기업 조사는 **그룹 전체**의 지배구조와 자금 흐름을 파악하는 것이 중요합니다. 특히 **경영권 승계** 과정에서 발생하는 **불공정 자본거래**(합병, 증자 등)가 핵심입니다. 또한, **총수 일가** 지분이 높은 계열사에 **일감 몰아주기**, **통행세** 거래 등을 통해 부당한 이익을 제공하는 행위도 주요 적발 사례입니다. 해외 현지법인을 이용한 **부당 지원** 및 **수수료** 지급도 추적 대상입니다.""",
        tactics=[
            EvasionTactic("일감 몰아주기 (통행세)", "**총수 자녀 회사**를 거래 중간에 끼워넣어 **통행세** 명목으로 연 500억원 부당 지원.", 500, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL),
            EvasionTactic("불공정 합병", "**총수 일가**에 유리하게 **계열사 합병 비율**을 산정하여 **이익** 200억원 증여.", 300, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL),
            EvasionTactic("해외 현지법인 부당 지원", "**싱가포르 자회사**에 **업무 관련성** 없는 **컨설팅 수수료** 명목으로 400억원 부당 지급.", 400, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE)
        ],
        defense_actions=["대형 로펌 '**태평양**' 자문, '경영상 판단' 주장.", "공정위 등 타 부처 심의 결과 제시하며 반박.", "언론 통해 '**반기업 정서**' 프레임 활용.", "국회 통한 입법 로비 시도."],
        difficulty_tier=DifficultyTier.HARD
    ),
    Company(
        name="(주)씨엔해운 (C&N)", size="대기업", revenue=12_000_000, operating_income=600_000, tax_target=1600, team_hp_damage=(25, 45),
        description="'**해운 재벌**'로 불리는 오너 운영. **조세피난처 SPC** 활용 및 **선박금융** 관련 복잡한 거래 구조.",
        real_case_desc="""[교육] 해운업과 같이 **자본 집약적**이고 **국제적** 성격 강한 산업은 **조세피난처**를 이용한 탈세 유인이 큽니다. **BVI, 라이베리아** 등에 설립한 **특수목적회사(SPC)** 명의로 선박을 운용하며 발생한 **운항 소득**을 국내에 신고 누락하거나, **노후 선박**을 이들 SPC에 **저가 양도**한 후 제3자에 **고가 매각**하여 양도 차익을 해외에 은닉하는 방식이 대표적인 역외탈세 사례입니다.""",
        tactics=[
            EvasionTactic("역외탈세 (SPC 소득 은닉)", "**라이베리아** 등 **SPC** 명의 선박 **운항 소득** 1조 2천억원을 국내 미신고 및 해외 은닉.", 1000, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.REVENUE),
            EvasionTactic("선박 매각 차익 은닉", "**노후 선박**을 해외 SPC에 **저가** 양도 후, SPC가 제3자에 **고가** 매각하는 방식 **양도 차익** 600억원 해외 은닉.", 600, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.CAPITAL)
        ],
        defense_actions=["해외 SPC는 '독립된 법인격' 주장.", "국제 해운 관행 및 현지 법률 준수 항변.", "**조세정보교환협정** 미체결국 이용, 자료 확보 방해.", "해운 불황으로 인한 '경영상 어려움' 호소."],
        difficulty_tier=DifficultyTier.HARD
    ),
    # --- S Group (Expert) ---
    Company(
        name="구굴 코리아(유) (Googul)", size="글로벌 기업", revenue=3_000_000, operating_income=400_000, tax_target=1000, team_hp_damage=(18, 35),
        description="글로벌 **IT 공룡**의 한국 지사. **디지털 광고**, **클라우드** 사업 영위.",
        real_case_desc="""[교육] **디지털세** 논의를 촉발한 글로벌 IT 기업들은 **고정사업장** 개념 회피, **이전가격 조작** 등 지능적 조세회피 전략을 사용합니다:
* **고정사업장 회피**: 국내 **서버** 운영, **국내 직원**이 핵심 계약 수행 등 실질적 사업 활동에도 불구, **단순 연락사무소** 또는 **자회사** 역할만 한다고 주장하여 **국내 원천소득** 과세 회피.
* **이전가격(TP) 조작**: **아일랜드, 싱가포르** 등 **저세율국** 관계사에 **IP 사용료**, **경영지원 수수료** 등을 과다 지급하여 국내 소득 축소. **정상가격 산출 방법**의 적정성 여부가 핵심 쟁점.
* **디지털 서비스 소득**: 국내 이용자 대상 **광고 수익**, **클라우드 서비스** 제공 대가 등의 **원천지** 규명 및 과세 문제.""",
        tactics=[
            EvasionTactic("이전가격(TP) 조작 - 경영지원료", "**싱가포르 지역본부**에 **실제 역할** 대비 과도한 **경영지원 수수료** 600억원 지급, 국내 이익 축소.", 600, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL),
            EvasionTactic("고정사업장 회피", "국내 **클라우드 서버** 운영 및 **기술 지원** 인력이 **핵심적 역할** 수행함에도 **고정사업장** 미신고, 관련 소득 400억원 과세 회피.", 400, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE)
        ],
        defense_actions=["미국 본사 '**기술 이전 계약**' 근거 정상 거래 주장.", "**조세 조약** 및 **OECD 가이드라인** 해석 다툼 예고.", "**상호합의절차(MAP)** 신청 통한 시간 끌기 전략.", "각국 과세 당국 간 **정보 부족** 악용."],
        difficulty_tier=DifficultyTier.EXPERT
    ),
    Company(
        name="아메존 코리아 (Amejon)", size="글로벌 기업", revenue=20_000_000, operating_income=500_000, tax_target=1800, team_hp_damage=(30, 50),
        description="세계 최대 **E-커머스** 및 **클라우드 서비스** 기업. 국내 **물류센터** 운영 및 **AWS** 사업 활발.",
        real_case_desc="""[교육] **클라우드 컴퓨팅** 및 **E-커머스** 기업은 **서버**와 **물류센터**의 법적 성격이 핵심 쟁점입니다.
* **고정사업장(PE) 쟁점**: 국내 **데이터센터(서버)**나 **물류창고**가 단순 **보관/지원** 기능을 넘어 **핵심 사업 활동**을 수행하는지 여부. **고정사업장**으로 판명 시 막대한 **법인세** 추징 가능.
* **이전가격(TP) 조작**: **클라우드 사용료**, **오픈마켓 수수료** 수익 등을 **저세율국** 본사 또는 관계사로 이전하고, 국내 법인에는 최소한의 **지원 용역 수수료**만 배분.
* **부가세**: **클라우드 서비스**가 '**국외 공급 용역**'인지 '**국내 공급 용역**'인지에 따라 **부가세** 과세 여부 달라짐.""",
        tactics=[
            EvasionTactic("고정사업장(PE) 회피", "국내 **대규모 데이터센터(IDC)**가 **클라우드 서비스**의 **핵심 사업** 수행함에도 **'예비적/보조적' 활동**이라 주장하며 관련 **법인세** 1조원 신고 누락.", 1000, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE),
            EvasionTactic("이전가격 조작 - 로열티", "국내 **E-커머스** 사업 수익 대부분을 **'브랜드 사용료'** 및 **'플랫폼 로열티'** 명목으로 **룩셈부르크** 본사에 과다 지급.", 800, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL)
        ],
        defense_actions=["**조세 조약** 상 고정사업장 정의에 미부합 주장.", "클라우드 서버는 '단순 저장 장치'라고 항변.", "미국 **IRS**와의 **이중과세** 문제 제기 (MAP).", "한국 정부 '디지털세' 도입 반대 로비."],
        difficulty_tier=DifficultyTier.EXPERT
    ),
]

# --- 3. 게임 로직 함수 ---

def initialize_game(chosen_lead: TaxManCard, chosen_artifact: Artifact):
    """게임 초기화"""
    team_members = [chosen_lead]
    all_mem = list(TAX_MAN_DB.values())
    remain = [m for m in all_mem if m.name != chosen_lead.name]
    team_members.extend(random.sample(remain, min(2, len(remain))))
    st.session_state.player_team = team_members

    start_deck = [
        LOGIC_CARD_DB["basic_01"], LOGIC_CARD_DB["basic_01"],
        LOGIC_CARD_DB["basic_02"],
        LOGIC_CARD_DB["b_tier_04"],
        LOGIC_CARD_DB["c_tier_02"], LOGIC_CARD_DB["c_tier_02"],
        LOGIC_CARD_DB["c_tier_01"], LOGIC_CARD_DB["c_tier_01"], LOGIC_CARD_DB["c_tier_01"],
        LOGIC_CARD_DB["c_tier_01"], LOGIC_CARD_DB["c_tier_01"]
    ]

    st.session_state.player_deck = random.sample(start_deck, len(start_deck))
    st.session_state.player_hand = []
    st.session_state.player_discard = []
    st.session_state.player_artifacts = [chosen_artifact]

    # ⭐ 이 부분 추가: team_hp를 삭제하여 강제로 재설정
    if 'team_hp' in st.session_state:
        del st.session_state['team_hp']
    
    recalculate_team_stats()

    all_companies = sorted(COMPANY_DB, key=lambda x: x.tax_target)
    group_c = [c for c in all_companies if c.difficulty_tier == DifficultyTier.EASY]
    group_b = [c for c in all_companies if c.difficulty_tier == DifficultyTier.MEDIUM]
    group_a = [c for c in all_companies if c.difficulty_tier == DifficultyTier.HARD]
    group_s = [c for c in all_companies if c.difficulty_tier == DifficultyTier.EXPERT]

    stage1 = random.choice(group_c) if group_c else all_companies[0]
    stage2 = random.choice(group_b) if group_b else all_companies[1]
    stage3 = random.choice(group_a) if group_a else all_companies[2]
    stage4 = random.choice(group_s) if group_s else all_companies[3]

    st.session_state.company_order = [stage1, stage2, stage3, stage4]

    st.session_state.current_battle_company = None
    st.session_state.battle_log = []
    st.session_state.selected_card_index = None
    st.session_state.bonus_draw = 0
    st.session_state.game_state = "MAP"
    st.session_state.current_stage_level = 0
    st.session_state.total_collected_tax = 0
    st.session_state.battle_stats = {
        'turns_taken': 0,
        'cards_played': 0,
        'total_damage_dealt': 0,
        'tactics_cleared': 0
    }

def recalculate_team_stats():
    """팀 스탯 재계산"""
    team_members = st.session_state.player_team
    st.session_state.team_max_hp = sum(m.hp for m in team_members)
    
    if 'team_hp' in st.session_state:
        st.session_state.team_hp = min(st.session_state.team_hp, st.session_state.team_max_hp)
    else:
        st.session_state.team_hp = st.session_state.team_max_hp

    st.session_state.player_focus_max = sum(m.focus for m in team_members)
    
    if 'player_focus_current' in st.session_state:
        st.session_state.player_focus_current = min(st.session_state.player_focus_current, st.session_state.player_focus_max)
    else:
        st.session_state.player_focus_current = st.session_state.player_focus_max

    st.session_state.team_stats = {
        "analysis": sum(m.analysis for m in team_members),
        "persuasion": sum(m.persuasion for m in team_members),
        "evidence": sum(m.evidence for m in team_members),
        "data": sum(m.data for m in team_members)
    }
    
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_battle_start":
            if art.effect["subtype"] == "stat_evidence":
                st.session_state.team_stats["evidence"] += art.effect["value"]
            elif art.effect["subtype"] == "stat_persuasion":
                st.session_state.team_stats["persuasion"] += art.effect["value"]
            elif art.effect["subtype"] == "stat_analysis":
                st.session_state.team_stats["analysis"] += art.effect["value"]

def start_player_turn():
    """플레이어 턴 시작"""
    st.session_state.hit_effect_player = False
    st.session_state.battle_stats['turns_taken'] += 1

    st.session_state.player_focus_max = sum(m.focus for m in st.session_state.player_team)
    st.session_state.player_focus_current = st.session_state.player_focus_max

    if "임향수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current += 1
        log_message("✨ [기획 조사] 집중력 +1!", "info")
    
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_turn_start" and art.effect["subtype"] == "focus":
            st.session_state.player_focus_current += art.effect["value"]
            log_message(f"✨ {art.name} 집중력 +{art.effect['value']}!", "info")
    
    st.session_state.player_focus_current = min(st.session_state.player_focus_current, st.session_state.player_focus_max + 10)

    if "김대조" in [m.name for m in st.session_state.player_team] and st.session_state.team_stats["data"] >= 50 and not st.session_state.get('kim_dj_effect_used', False):
        new = copy.deepcopy(LOGIC_CARD_DB["b_tier_01"])
        new.just_created = True
        st.session_state.player_hand.append(new)
        log_message("✨ [부동산 조사] '금융거래 분석' 1장 획득!", "info")
        st.session_state.kim_dj_effect_used = True
    
    st.session_state.cost_reduction_active = "전준" in [m.name for m in st.session_state.player_team]
    if st.session_state.cost_reduction_active:
        log_message("✨ [실무 지휘] 다음 카드 비용 -1!", "info")

    st.session_state.bonus_draw = 0
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_battle_start" and art.effect["subtype"] == "draw":
            st.session_state.bonus_draw += art.effect["value"]

    draw_n = 4 + st.session_state.get('bonus_draw', 0)
    is_first_turn = not st.session_state.battle_log or (len(st.session_state.battle_log) > 0 and "조사 시작" in st.session_state.battle_log[-1])
    
    if st.session_state.get('bonus_draw', 0) > 0 and is_first_turn:
        log_message(f"✨ 시작 보너스로 카드 {st.session_state.bonus_draw}장 추가 드로우!", "info")

    draw_cards(draw_n)
    check_draw_cards_in_hand()
    log_message("--- 플레이어 턴 시작 ---")
    st.session_state.turn_first_card_played = True
    st.session_state.selected_card_index = None

def draw_cards(num):
    """카드 드로우"""
    try:
        drawn = []
        for _ in range(num):
            if not st.session_state.player_deck:
                if not st.session_state.player_discard:
                    log_message("경고: 더 뽑을 카드 없음!", "error")
                    break
                log_message("덱 리셔플.")
                st.session_state.player_deck = random.sample(st.session_state.player_discard, len(st.session_state.player_discard))
                st.session_state.player_discard = []
                if not st.session_state.player_deck:
                    log_message("경고: 덱/버린 덱 모두 비었음!", "error")
                    break
            if not st.session_state.player_deck:
                log_message("경고: 덱 비었음!", "error")
                break
            card = st.session_state.player_deck.pop()
            drawn.append(card)
        st.session_state.player_hand.extend(drawn)
    except Exception as e:
        log_message(f"⚠️ 카드 드로우 오류: {str(e)}", "error")

def check_draw_cards_in_hand():
    """손패의 드로우 카드 자동 실행"""
    try:
        indices = [i for i, c in enumerate(st.session_state.player_hand) 
                  if c.cost == 0 and c.special_effect and c.special_effect.get("type") == "draw" 
                  and not getattr(c, 'just_created', False)]
        indices.reverse()
        total_draw = 0
        
        for idx in indices:
            if idx < len(st.session_state.player_hand):
                card = st.session_state.player_hand.pop(idx)
                st.session_state.player_discard.append(card)
                val = card.special_effect.get('value', 0)
                log_message(f"✨ [{card.name}] 효과! 카드 {val}장 뽑기.", "info")
                
                if "조용규" in [m.name for m in st.session_state.player_team] and card.name == "법령 재검토":
                    log_message("✨ [세법 교본] +1장 추가!", "info")
                    val *= 2
                
                total_draw += val
            else:
                log_message(f"경고: 드로우 처리 인덱스 오류 (idx: {idx})", "error")
        
        for card in st.session_state.player_hand:
            if hasattr(card, 'just_created'):
                card.just_created = False
        
        if total_draw > 0:
            draw_cards(total_draw)
    except Exception as e:
        log_message(f"⚠️ 드로우 카드 처리 오류: {str(e)}", "error")

def calculate_card_cost(card):
    """카드 비용 계산"""
    try:
        original_cost = max(0, card.cost - 1)
        cost = original_cost

        if "백용호" in [m.name for m in st.session_state.player_team] and ('데이터' in card.name or '분석' in card.name or AttackCategory.CAPITAL in card.attack_category):
            cost = max(0, cost - 1)
        
        is_first = st.session_state.get('turn_first_card_played', True)
        type_match = ('분석' in card.name or '판례' in card.name or '법령' in card.name or AttackCategory.COMMON in card.attack_category)
        
        if "박조연" in [m.name for m in st.session_state.player_team] and is_first and type_match:
            cost = max(0, cost - 1)
        
        if "안원규" in [m.name for m in st.session_state.player_team] and card.name in ['현장 압수수색', '차명계좌 추적']:
            cost = max(0, cost - 1)
        
        if st.session_state.get('cost_reduction_active', False):
            cost = max(0, cost - 1)

        for art in st.session_state.player_artifacts:
            if art.effect["type"] == "on_cost_calculate" and card.name in art.effect["target_cards"]:
                cost = max(0, cost + art.effect["value"])

        final_cost = max(0, cost + 1)
        return final
        _cost
    except Exception as e:
        log_message(f"⚠️ 카드 비용 계산 오류: {str(e)}", "error")
        return card.cost

def execute_utility_card(card_index):
    """유틸리티 카드 실행 (드로우, 서치 등)"""
    try:
        if card_index is None or card_index >= len(st.session_state.player_hand):
            return
        
        card = st.session_state.player_hand[card_index]
        cost = calculate_card_cost(card)
        
        if st.session_state.player_focus_current < cost:
            st.toast(f"집중력 부족! ({cost})", icon="🧠")
            return

        original_cost_plus_one = max(0, card.cost - 1) + 1
        if st.session_state.get('cost_reduction_active', False) and cost < original_cost_plus_one:
            st.session_state.cost_reduction_active = False
            st.session_state.cost_reduction_active_just_used = True

        st.session_state.player_focus_current -= cost
        st.session_state.battle_stats['cards_played'] += 1
        
        if st.session_state.get('turn_first_card_played', True):
            st.session_state.turn_first_card_played = False
        
        effect = card.special_effect.get("type")
        
        if effect == "search_draw":
            cats = list(set([t.tactic_category for t in st.session_state.current_battle_company.tactics if not t.is_cleared]))
            if not cats:
                log_message("ℹ️ [빅데이터 분석] 분석할 혐의 없음.", "info")
            else:
                pool = st.session_state.player_deck + st.session_state.player_discard
                random.shuffle(pool)
                found = next((c for c in pool 
                            if c not in st.session_state.player_hand 
                            and c.cost > 0 
                            and AttackCategory.COMMON not in c.attack_category 
                            and not (c.special_effect and c.special_effect.get("type") == "draw") 
                            and any(cat in cats for cat in c.attack_category)), None)
                
                if found:
                    log_message(f"📊 [빅데이터 분석] '{found.name}' 발견!", "success")
                    new = copy.deepcopy(found)
                    new.just_created = True
                    st.session_state.player_hand.append(new)
                    try:
                        st.session_state.player_deck.remove(found)
                    except ValueError:
                        try:
                            st.session_state.player_discard.remove(found)
                        except ValueError:
                            log_message("경고: 빅데이터 카드 제거 오류", "error")
                else:
                    log_message("ℹ️ [빅데이터 분석] 관련 카드 없음...", "info")
        
        elif effect == "draw":
            val = card.special_effect.get("value", 0)
            log_message(f"✨ [{card.name}] 효과! 카드 {val}장 드로우!", "info")
            draw_cards(val)

        if st.session_state.get('cost_reduction_active_just_used', False):
            log_message(f"✨ [실무 지휘] 카드 비용 -1 적용!", "info")
            st.session_state.cost_reduction_active_just_used = False

        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
        st.session_state.selected_card_index = None
        check_draw_cards_in_hand()
        st.rerun()
    
    except Exception as e:
        log_message(f"⚠️ 유틸리티 카드 실행 오류: {str(e)}", "error")

def select_card_to_play(card_index):
    """카드 선택"""
    try:
        if 'player_hand' not in st.session_state or card_index >= len(st.session_state.player_hand):
            st.toast("오류: 유효 카드 아님.", icon="🚨")
            return
        
        card = st.session_state.player_hand[card_index]
        cost = calculate_card_cost(card)
        
        if st.session_state.player_focus_current < cost:
            st.toast(f"집중력 부족! ({cost})", icon="🧠")
            return
        
        if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]:
            execute_utility_card(card_index)
        else:
            st.session_state.selected_card_index = card_index
            st.rerun()
    
    except Exception as e:
        log_message(f"⚠️ 카드 선택 오류: {str(e)}", "error")

def cancel_card_selection():
    """카드 선택 취소"""
    st.session_state.selected_card_index = None
    st.rerun()

def execute_attack(card_index, tactic_index, penalty_mult=1.0):
    """공격 실행"""
    try:
        if card_index is None or card_index >= len(st.session_state.player_hand):
            st.toast("오류: 잘못된 카드 인덱스.", icon="🚨")
            st.session_state.selected_card_index = None
            st.rerun()
            return
        
        card = st.session_state.player_hand[card_index]
        cost = calculate_card_cost(card)
        company = st.session_state.current_battle_company
        is_residual = tactic_index >= len(company.tactics)
        tactic = ResidualTactic(company.tax_target - company.current_collected_tax) if is_residual else company.tactics[tactic_index]
        
        if st.session_state.player_focus_current < cost:
            st.toast(f"집중력 부족! ({cost})", icon="🧠")
            st.session_state.selected_card_index = None
            st.rerun()
            return

        original_cost_plus_one = max(0, card.cost - 1) + 1
        if st.session_state.get('cost_reduction_active', False) and cost < original_cost_plus_one:
            st.session_state.cost_reduction_active = False
            st.session_state.cost_reduction_active_just_used = True

        st.session_state.player_focus_current -= cost
        st.session_state.battle_stats['cards_played'] += 1
        
        if st.session_state.get('turn_first_card_played', True):
            st.session_state.turn_first_card_played = False

        # 대미지 계산기 사용
        calc = DamageCalculator(
            card, tactic, company, 
            st.session_state.player_team, 
            st.session_state.team_stats,
            st.session_state.current_stage_level
        )
        damage_result = calc.calculate(penalty_mult)
        final_dmg = damage_result['final_damage']
        
        # 대미지 적용
        overkill = 0
        overkill_contrib = 0

        if is_residual:
            dmg_tactic = final_dmg
        else:
            remain = tactic.total_amount - tactic.exposed_amount
            dmg_tactic = min(final_dmg, remain)
            overkill = final_dmg - dmg_tactic
            overkill_contrib = int(overkill * 0.5)
            tactic.exposed_amount += dmg_tactic
        
        company.current_collected_tax += (dmg_tactic + overkill_contrib)
        st.session_state.battle_stats['total_damage_dealt'] += (dmg_tactic + overkill_contrib)

        # 공격 이펙트 표시
        attack_emoji = "💥"
        prefix = "▶️ [적중]"
        is_crit = damage_result['multiplier'] >= 2.0

        dmg_ratio = final_dmg / company.tax_target if company.tax_target > 0 else 0
        hit_level = 0
        
        if is_crit or dmg_ratio > 0.3:
            hit_level = 3
            prefix = "💥💥 [초 치명타!]"
            st.balloons()
        elif damage_result['multiplier'] > 1.0 or dmg_ratio > 0.15:
            hit_level = 2
            prefix = "🔥🔥 [치명타!]"
        elif final_dmg > 0:
            hit_level = 1
            prefix = "👍 [효과적!]"
        
        st.session_state.hit_effect_company = hit_level

        if AttackCategory.COST in card.attack_category:
            attack_emoji = "💸"
        elif AttackCategory.REVENUE in card.attack_category:
            attack_emoji = "📈"
        elif AttackCategory.CAPITAL in card.attack_category:
            attack_emoji = "🏦"
        elif card.name == "현장 압수수색":
            attack_emoji = "🔎"
        elif card.name == "판례 제시":
            attack_emoji = "⚖️"
        elif AttackCategory.COMMON in card.attack_category:
            attack_emoji = "📄"

        st.toast(f"{attack_emoji} {final_dmg}억원!", icon=attack_emoji)

        log_message(f"{prefix} '{card.name}' → '{tactic.name}'에 **{final_dmg}억원** 피해!", "success")
        
        # 계산 로그 출력
        for log in damage_result['logs']:
            log_message(f"  ㄴ {log}", "info")
        
        for mult_desc in damage_result['multiplier_desc']:
            log_message(f"  ㄴ {mult_desc}", "info")
        
        if penalty_mult != 1.0:
            log_message(f"  ㄴ 🤖 [자동공격 페널티 x{penalty_mult:.2f}]", "info")
        
        if st.session_state.get('cost_reduction_active_just_used', False):
            log_message(f"✨ [실무 지휘] 카드 비용 -1 적용!", "info")
            st.session_state.cost_reduction_active_just_used = False

        # 교육 팁 표시
        tips = EducationalSystem.get_attack_tip(card, tactic, damage_result['multiplier'])
        for tip in tips:
            log_message(tip, "info")

        # 상황별 메시지
        if not is_residual:
            if "금융" in card.name:
                log_message(f"💬 금융 분석팀: 의심스러운 자금 흐름 포착!", "info")
            elif "차명" in card.name:
                log_message(f"💬 조사팀: 은닉 계좌 추적 성공! 자금 흐름 확보!", "warning")
            elif "압수" in card.name:
                log_message(f"💬 현장팀: 결정적 증거물 확보!", "warning")
            elif "출처" in card.name:
                log_message(f"💬 조사팀: 자금 출처 소명 요구, 압박 수위 높임!", "info")
            elif tactic.method_type == MethodType.INTENTIONAL and final_dmg > tactic.total_amount * 0.5:
                log_message(f"💬 조사팀: 고의적 탈루 정황 가중! 추가 조사 필요.", "warning")
            elif tactic.method_type == MethodType.ERROR and '판례' in card.name:
                log_message(f"💬 법무팀: 유사 판례 제시하여 납세자 설득 중...", "info")
            
            if final_dmg < 10 and damage_result['base_damage'] > 0:
                log_message(f"💬 조사관: 꼼꼼하게 증빙 대조 중...", "info")
            elif final_dmg > 100:
                log_message(f"💬 조사팀장: 결정적인 한 방입니다!", "success")
        
        if overkill > 0:
            log_message(f"📈 [초과 기여] 혐의 초과 {overkill}억 중 {overkill_contrib}억 추가 세액 확보!", "info")

        if not is_residual and tactic.exposed_amount >= tactic.total_amount and not getattr(tactic, '_logged_clear', False):
            setattr(tactic, 'is_cleared', True)
            setattr(tactic, '_logged_clear', True)
            st.session_state.battle_stats['tactics_cleared'] += 1
            log_message(f"🔥 [{tactic.name}] 혐의 완전 적발 완료! (총 {tactic.total_amount}억원)", "warning")
            
            if "벤츠" in card.text:
                log_message("💬 [현장] 법인소유 벤츠 키 확보!", "info")
            if "압수수색" in card.name:
                log_message("💬 [현장] 비밀장부 및 관련 증거물 다수 확보!", "info")

        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
        st.session_state.selected_card_index = None
        check_battle_end()
        st.rerun()
    
    except Exception as e:
        log_message(f"⚠️ 공격 실행 오류: {str(e)}", "error")
        st.error(f"공격 실행 중 오류가 발생했습니다: {e}")

def execute_auto_attack():
    """자동 공격"""
    try:
        hp_cost = 5
        if st.session_state.team_hp <= hp_cost:
            st.toast(f"⚡ 자동 공격을 사용하기엔 팀 체력이 너무 낮습니다! (최소 {hp_cost+1} 필요)", icon="💔")
            return

        affordable_attacks = []
        for i, card in enumerate(st.session_state.player_hand):
            if card.base_damage <= 0 or (card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]):
                continue
            cost = calculate_card_cost(card)
            if st.session_state.player_focus_current >= cost:
                affordable_attacks.append({'card': card, 'index': i, 'cost': cost})
        
        affordable_attacks.sort(key=lambda x: x['card'].base_damage, reverse=True)
        
        if not affordable_attacks:
            st.toast("⚡ 사용할 수 있는 자동 공격 카드가 없습니다.", icon="⚠️")
            return

        company = st.session_state.current_battle_company
        attack_executed = False
        all_tactics_cleared = all(t.is_cleared for t in company.tactics)
        target_not_met = company.current_collected_tax < company.tax_target

        for attack_info in affordable_attacks:
            current_card = attack_info['card']
            current_idx = attack_info['index']
            target_idx = -1
            
            if not all_tactics_cleared:
                for i, t in enumerate(company.tactics):
                    if t.is_cleared:
                        continue
                    
                    card_tax_values = get_enum_values(current_card.tax_type)
                    tactic_tax_values = get_enum_values(t.tax_type)
                    is_tax = (TaxType.COMMON.value in card_tax_values) or any(ttv in card_tax_values for ttv in tactic_tax_values)
                    
                    card_cat_values = get_enum_values(current_card.attack_category)
                    tactic_cat_value = safe_get_enum_value(t.tactic_category)
                    is_cat = (AttackCategory.COMMON.value in card_cat_values) or (tactic_cat_value in card_cat_values)
                    
                    if is_tax and is_cat:
                        target_idx = i
                        break
            elif all_tactics_cleared and target_not_met:
                target_idx = len(company.tactics)

            if target_idx != -1:
                st.session_state.team_hp -= hp_cost
                log_message(f"⚡ 자동 공격 사용! (팀 체력 -{hp_cost}, 피해량 25% 감소)", "warning")
                st.toast(f"⚡ 자동 공격! (❤️-{hp_cost}, 💥-25%)", icon="🤖")
                
                target_name = "[잔여 혐의 조사]" if target_idx >= len(company.tactics) else company.tactics[target_idx].name
                log_message(f"⚡ 자동 공격: '{current_card.name}' -> '{target_name}'!", "info")

                execute_attack(current_idx, target_idx, penalty_mult=0.75)
                attack_executed = True
                break

        if not attack_executed:
            st.toast(f"⚡ 현재 손패의 카드로 공격 가능한 혐의가 없습니다.", icon="⚠️")
    
    except Exception as e:
        log_message(f"⚠️ 자동 공격 오류: {str(e)}", "error")

def develop_tax_logic():
    """과세 논리 개발"""
    try:
        hp_cost = math.ceil(st.session_state.team_hp / 2)
        if st.session_state.team_hp <= 1 or (st.session_state.team_hp - hp_cost) <= 0:
            st.toast("💡 체력이 너무 낮아 과세 논리를 개발할 수 없습니다.", icon="💔")
            return

        st.session_state.team_hp -= hp_cost

        company = st.session_state.current_battle_company
        remaining_tactics = [t for t in company.tactics if not t.is_cleared]
        all_cleared = not remaining_tactics
        target_not_met = company.current_collected_tax < company.tax_target

        target_cats = set()
        target_methods = set()

        if remaining_tactics:
            for t in remaining_tactics:
                cat_val = safe_get_enum_value(t.tactic_category)
                if cat_val:
                    target_cats.add(cat_val)
                
                tax_values = get_enum_values(t.tax_type)
                target_cats.update(tax_values)
                target_methods.add(t.method_type)
        elif all_cleared and target_not_met:
            target_cats.add(AttackCategory.COMMON.value)
            target_methods.add(MethodType.ERROR)
        else:
            st.toast("💡 더 이상 분석할 혐의가 없습니다.", icon="ℹ️")
            st.session_state.team_hp += hp_cost
            return

        best_card = None
        max_score = -1

        for card in LOGIC_CARD_DB.values():
            if card.base_damage <= 0 or (card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]):
                continue

            card_cats_values = get_enum_values(card.attack_category)
            is_cat_match = (AttackCategory.COMMON.value in card_cats_values) or any(cat_val in target_cats for cat_val in card_cats_values)

            if not is_cat_match:
                continue

            score = card.base_damage

            if card.special_bonus and card.special_bonus.get('target_method') in target_methods:
                score *= card.special_bonus.get('multiplier', 1.0) * 1.5

            card_actual_cost = calculate_card_cost(card)
            if card_actual_cost > 3:
                score *= 0.8
            if card_actual_cost <= 1 and card.base_damage > 0:
                score *= 1.1

            if score > max_score:
                max_score = score
                best_card = card

        if best_card:
            new_card = copy.deepcopy(best_card)
            new_card.just_created = True
            st.session_state.player_hand.append(new_card)
            log_message(f"💡 [과세 논리 개발] '{best_card.name}' 획득! (팀 체력 -{hp_cost})", "warning")
            st.toast(f"💡 '{best_card.name}' 획득! (❤️-{hp_cost})", icon="💡")
            st.session_state.hit_effect_player = True
        else:
            log_message("💡 [과세 논리 개발] 적절한 카드를 찾지 못함.", "info")
            st.toast("💡 적절한 카드를 찾지 못했습니다.", icon="ℹ️")
            st.session_state.team_hp += hp_cost

        st.rerun()
    
    except Exception as e:
        log_message(f"⚠️ 과세 논리 개발 오류: {str(e)}", "error")

def end_player_turn():
    """플레이어 턴 종료"""
    try:
        if 'kim_dj_effect_used' in st.session_state:
            st.session_state.kim_dj_effect_used = False
        if 'cost_reduction_active' in st.session_state:
            st.session_state.cost_reduction_active = False
        if 'cost_reduction_active_just_used' in st.session_state:
            st.session_state.cost_reduction_active_just_used = False
        
        st.session_state.player_discard.extend(st.session_state.player_hand)
        st.session_state.player_hand = []
        st.session_state.selected_card_index = None
        
        log_message("--- 기업 턴 시작 ---")
        enemy_turn()
        
        if not check_battle_end():
            start_player_turn()
            st.rerun()
    
    except Exception as e:
        log_message(f"⚠️ 턴 종료 오류: {str(e)}", "error")

def enemy_turn():
    """적 턴"""
    try:
        co = st.session_state.current_battle_company
        act = random.choice(co.defense_actions)
        min_d, max_d = co.team_hp_damage
        dmg = random.randint(min_d, max_d)
        st.session_state.team_hp -= dmg
        st.session_state.hit_effect_player = True
        
        st.toast(f"❤️ 팀 체력 -{dmg}!", icon="💔")
        
        log_icon = "🏢"
        if "로펌" in act or "법무팀" in act or "법리" in act:
            log_icon = "⚖️"
        elif "자료" in act or "서버" in act or "장부" in act:
            log_icon = "📁"
        elif "압력" in act or "여론전" in act or "항변" in act:
            log_icon = "🗣️"
        elif "도피" in act or "잠적" in act or "시간" in act:
            log_icon = "⏳"
        
        prefix = f"{log_icon} [기업]" if not (co.size in ["대기업", "외국계", "글로벌 기업"] and "로펌" in act) else f"{log_icon} [로펌]"
        log_message(f"{prefix} {act} (팀 사기 저하 ❤️-{dmg}!)", "error")
    
    except Exception as e:
        log_message(f"⚠️ 적 턴 오류: {str(e)}", "error")

def check_battle_end():
    """전투 종료 체크"""
    try:
        company = st.session_state.current_battle_company
        
        if company.current_collected_tax >= company.tax_target:
            bonus = company.current_collected_tax - company.tax_target
            log_message(f"🎉 [조사 승리] 목표 {company.tax_target:,}억원 달성! (초과 {bonus:,}억원)", "success")
            st.session_state.total_collected_tax += company.current_collected_tax

            heal_amount = int(st.session_state.team_max_hp * 0.3)
            st.session_state.team_hp = min(st.session_state.team_max_hp, st.session_state.team_hp + heal_amount)
            log_message(f"🩺 [전투 승리] 팀 정비. (체력 +{heal_amount})", "success")
            
            last_card_text = ""
            if st.session_state.player_discard:
                try:
                    last_card_text = st.session_state.player_discard[-1].text
                except IndexError:
                    pass
            
            st.toast(f"승리! \"{last_card_text}\"" if last_card_text else "승리!", icon="🎉")

            st.session_state.bonus_reward_artifact = None
            st.session_state.bonus_reward_member = None
            next_state = "REWARD"

            if random.random() < 0.34:
                current_artifact_names = [art.name for art in st.session_state.player_artifacts]
                available_artifacts = [art for art in ARTIFACT_DB.values() if art.name not in current_artifact_names]
                if available_artifacts:
                    new_artifact = random.choice(available_artifacts)
                    st.session_state.bonus_reward_artifact = new_artifact
                    log_message(f"🎁 [전리품 발견] 새로운 조사 도구 '{new_artifact.name}' 발견!", "info")
                    next_state = "REWARD_BONUS"

            if next_state != "REWARD_BONUS" and random.random() < 0.49:
                current_member_names = [m.name for m in st.session_state.player_team]
                available_members = [m for m in TAX_MAN_DB.values() if m.name not in current_member_names]
                if available_members:
                    new_member = random.choice(available_members)
                    st.session_state.bonus_reward_member = new_member
                    log_message(f"👥 [지원군 발견] '{new_member.name}' 조사관 발견!", "info")
                    next_state = "REWARD_BONUS"

            st.session_state.game_state = next_state
            return True

        if st.session_state.team_hp <= 0:
            st.session_state.team_hp = 0
            log_message("‼️ [조사 중단] 팀 체력 소진...", "error")
            st.session_state.game_state = "GAME_OVER"
            return True
        
        return False
    
    except Exception as e:
        log_message(f"⚠️ 전투 종료 체크 오류: {str(e)}", "error")
        return False

def start_battle(co_template):
    """전투 시작"""
    try:
        co = copy.deepcopy(co_template)
        st.session_state.current_battle_company = co
        st.session_state.game_state = "BATTLE"
        st.session_state.battle_log = [f"--- {co.name} ({co.size}) 조사 시작 ---"]
        
        log_message(f"🏢 **{co.name}** 주요 탈루 혐의:", "info")
        
        t_types = set()
        for t in co.tactics:
            tax_str = ', '.join(get_enum_values(t.tax_type))
            method_val = safe_get_enum_value(t.method_type, "메소드 오류")
            category_val = safe_get_enum_value(t.tactic_category, "카테고리 오류")

            log_message(f"- **{t.name}** ({tax_str}, {method_val}, {category_val})", "info")
            t_types.add(t.method_type)

        log_message("---", "info")
        guide = "[조사 가이드] "
        has_g = False
        
        if MethodType.INTENTIONAL in t_types:
            guide += "고의 탈루: 증거 확보, 압박 중요. "
            has_g = True
        if MethodType.CAPITAL_TX in t_types or co.size in ["대기업", "외국계", "글로벌 기업"]:
            guide += "자본/국제 거래: 자금 흐름, 법규 분석 필요. "
            has_g = True
        if MethodType.ERROR in t_types and MethodType.INTENTIONAL not in t_types:
            guide += "단순 오류: 규정/판례 제시, 설득 효과적. "
            has_g = True
        
        log_message(guide if has_g else "[조사 가이드] 기업 특성/혐의 고려, 전략적 접근.", "warning")
        log_message("---", "info")

        recalculate_team_stats()

        st.session_state.bonus_draw = 0
        for art in st.session_state.player_artifacts:
            log_message(f"✨ [조사도구] '{art.name}' 효과 준비.", "info")
            if art.effect["type"] == "on_battle_start" and art.effect["subtype"] == "draw":
                st.session_state.bonus_draw += art.effect["value"]

        st.session_state.player_deck.extend(st.session_state.player_discard)
        st.session_state.player_deck = random.sample(st.session_state.player_deck, len(st.session_state.player_deck))
        st.session_state.player_discard = []
        st.session_state.player_hand = []
        
        # 전투 통계 초기화
        st.session_state.battle_stats = {
            'turns_taken': 0,
            'cards_played': 0,
            'total_damage_dealt': 0,
            'tactics_cleared': 0
        }
        
        start_player_turn()
    
    except Exception as e:
        log_message(f"⚠️ 전투 시작 오류: {str(e)}", "error")

def log_message(message, level="normal"):
    """로그 메시지 추가"""
    try:
        color = {"success": "green", "warning": "orange", "error": "red", "info": "blue"}.get(level)
        msg = f":{color}[{message}]" if color else message
        
        if 'battle_log' not in st.session_state:
            st.session_state.battle_log = []
        
        st.session_state.battle_log.insert(0, msg)
        
        if len(st.session_state.battle_log) > 50:
            st.session_state.battle_log.pop()
    
    except Exception as e:
        st.error(f"로그 오류: {e}")

def go_to_next_stage(add_card=None):
    """다음 스테이지로"""
    try:
        if add_card:
            st.session_state.player_deck.append(add_card)
            st.toast(f"[{add_card.name}] 덱 추가!", icon="🃏")

        if 'reward_cards' in st.session_state:
            del st.session_state.reward_cards
        if 'bonus_reward_artifact' in st.session_state:
            st.session_state.bonus_reward_artifact = None
        if 'bonus_reward_member' in st.session_state:
            st.session_state.bonus_reward_member = None

        st.session_state.current_stage_level += 1
        
        if st.session_state.current_stage_level >= len(st.session_state.company_order):
            st.session_state.game_state = "GAME_CLEAR"
        else:
            st.session_state.game_state = "MAP"
        
        st.rerun()
    
    except Exception as e:
        log_message(f"⚠️ 스테이지 이동 오류: {str(e)}", "error")

# --- 4. UI 화면 함수 ---

def show_main_menu():
    """메인 메뉴"""
    st.title("💼 세무조사: 덱빌딩 로그라이크")
    st.markdown("---")

    st.markdown("<h1 style='text-align: center; font-size: 80px; margin-bottom: 0px;'>⚖️</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-top: 0px;'>국세청 조사국</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.header("국세청에 오신 것을 환영합니다.")
    st.markdown("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")

    if st.button("🚨 조사 시작", type="primary", use_container_width=True):
        members = list(TAX_MAN_DB.values())
        st.session_state.draft_team_choices = random.sample(members, min(len(members), 3))
        artifacts = list(ARTIFACT_DB.keys())
        chosen_keys = random.sample(artifacts, min(len(artifacts), 3))
        st.session_state.draft_artifact_choices = [ARTIFACT_DB[k] for k in chosen_keys]
        st.session_state.game_state = "GAME_SETUP_DRAFT"
        st.rerun()

    with st.expander("📖 게임 방법", expanded=True):
        st.markdown("""
        **1. 🎯 목표**: 총 4단계(중소기업→중견기업→대기업→글로벌기업)의 기업 조사를 완료하고 승리.
        
        **2. ⚔️ 전투**: 
        - ❤️ **팀 체력**(0이 되면 패배)
        - 🧠 **집중력**(카드 사용에 필요한 자원, 매 턴 회복)
        
        **3. 💡 전략**:
        - 혐의 유형(`고의`, `오류`, `자본`)에 맞는 카드 사용 시 추가 피해!
        - 팀 스탯(분석력, 설득력, 증거력, 데이터)을 활용한 카드 선택
        - 자동 공격(체력 -5, 피해량 -25%)과 과세 논리 개발(체력 50% 소모) 활용
        
        **4. 📈 성장**: 
        - 스테이지가 오를수록 기본 카드가 강해집니다
        - 전투 승리 시 확률적으로 **팀원**이나 **조사 도구** 획득!
        """)

    with st.expander("📚 세무 용어 사전"):
        for term, definition in EducationalSystem.GLOSSARY.items():
            st.markdown(f"**{term}**")
            st.caption(definition)
            st.divider()

    st.markdown(
        """<style>.watermark {position: fixed; top: 20px; left: 20px; opacity: 0.5; font-size: 14px; color: #777; z-index: 100;}</style><div class="watermark">제작자: 김현일 (중부청 조사0국 소속)</div>""",
        unsafe_allow_html=True
    )

def show_setup_draft_screen():
    """드래프트 화면"""
    st.title("👨‍💼 조사팀 구성")
    st.markdown("팀 **리더**와 시작 **조사도구** 선택:")
    
    if 'draft_team_choices' not in st.session_state or 'draft_artifact_choices' not in st.session_state:
        st.error("드래프트 정보 없음...")
        st.button("메인 메뉴로", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"))
        return
    
    teams = st.session_state.draft_team_choices
    arts = st.session_state.draft_artifact_choices
    
    st.markdown("---")
    st.subheader("1. 팀 리더 선택:")
    lead_idx = st.radio(
        "리더",
        range(len(teams)),
        format_func=lambda i: f"**{teams[i].name}** | {teams[i].description}\n    └ **{teams[i].ability_name}**: {teams[i].ability_desc}",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.subheader("2. 시작 조사도구 선택:")
    art_idx = st.radio(
        "도구",
        range(len(arts)),
        format_func=lambda i: f"**{arts[i].name}** | {arts[i].description}",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if st.button("이 구성으로 조사 시작", type="primary", use_container_width=True):
        initialize_game(teams[lead_idx], arts[art_idx])
        del st.session_state.draft_team_choices, st.session_state.draft_artifact_choices
        st.rerun()

def show_map_screen():
    """맵 화면"""
    if 'current_stage_level' not in st.session_state:
        st.warning("게임 상태 초기화됨...")
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()
        return

    stage = st.session_state.current_stage_level
    stage_total = len(st.session_state.company_order)
    
    difficulty_name = {
        0: "C 그룹 (중소기업)",
        1: "B 그룹 (중견기업)",
        2: "A 그룹 (대기업)",
        3: "S 그룹 (글로벌기업)"
    }.get(stage, "알 수 없음")
    
    st.header(f"📍 조사 지역 (Stage {stage + 1} / {stage_total}) - {difficulty_name}")
    st.write("조사할 기업 선택:")

    companies = st.session_state.company_order
    
    if stage < len(companies):
        co = companies[stage]
        
        with st.container(border=True):
            st.subheader(f"🏢 {co.name} ({co.size})")
            st.markdown(co.description)
            
            c1, c2 = st.columns(2)
            c1.metric("매출액", format_krw(co.revenue))
            c2.metric("영업이익", format_krw(co.operating_income))
            
            st.warning(f"**예상 턴당 데미지:** {co.team_hp_damage[0]}~{co.team_hp_damage[1]} ❤️")
            st.info(f"**목표 추징 세액:** {co.tax_target:,} 억원 💰")
            
            with st.expander("🔍 혐의 및 실제 사례 정보 보기"):
                st.markdown("---")
                st.markdown("### 📚 실제 사례 기반 교육 정보")
                st.markdown(co.real_case_desc)
                st.markdown("---")
                st.markdown("### 📝 주요 탈루 혐의 분석")

                if not co.tactics:
                    st.write("(분석할 특정 탈루 혐의 없음)")
                else:
                    for i, t in enumerate(co.tactics):
                        t_types_str = ', '.join(get_enum_values(t.tax_type))
                        method_val = safe_get_enum_value(t.method_type, "메소드 오류")
                        category_val = safe_get_enum_value(t.tactic_category, "카테고리 오류")
                        
                        st.markdown(f"**📌 {t.name}** (`{t_types_str}`, `{method_val}`, `{category_val}`)\n> _{t.description}_")

            if st.button(f"🚨 {co.name} 조사 시작", type="primary", use_container_width=True):
                start_battle(co)
                st.rerun()
    else:
        st.session_state.game_state = "GAME_CLEAR"
        st.rerun()

def show_battle_screen():
    """전투 화면"""
    if not st.session_state.current_battle_company:
        st.error("오류: 기업 정보 없음...")
        st.session_state.game_state = "MAP"
        st.rerun()
        return
    
    co = st.session_state.current_battle_company
    st.title(f"⚔️ {co.name} 조사 중...")
    st.markdown("---")
    
    col_co, col_log, col_hand = st.columns([1.6, 2.0, 1.4])
    
    with col_co:
        hit_level = st.session_state.get('hit_effect_company', 0)
        if hit_level == 3:
            st.error(f"💥💥💥 **{co.name} ({co.size})** 💥💥💥")
        elif hit_level == 2:
            st.warning(f"🔥🔥 **{co.name} ({co.size})** 🔥🔥")
        elif hit_level == 1:
            st.info(f"⚡ **{co.name} ({co.size})** ⚡")
        else:
            st.subheader(f"🏢 {co.name} ({co.size})")
        st.session_state.hit_effect_company = 0

        st.progress(
            min(1.0, co.current_collected_tax/co.tax_target if co.tax_target > 0 else 1.0),
            text=f"💰 목표 세액: {co.current_collected_tax:,}/{co.tax_target:,} (억원)"
        )
        st.markdown("---")
        st.subheader("🧾 탈루 혐의 목록")
        
        is_sel = st.session_state.get("selected_card_index") is not None
        if is_sel:
            if st.session_state.selected_card_index < len(st.session_state.player_hand):
                st.info(f"**'{st.session_state.player_hand[st.session_state.selected_card_index].name}'** 카드로 공격할 혐의 선택:")
            else:
                st.session_state.selected_card_index = None
                st.rerun()

        all_tactics_cleared = all(getattr(t, 'is_cleared', False) for t in co.tactics)
        target_not_met = co.current_collected_tax < co.tax_target

        tactic_cont = st.container(height=450)
        with tactic_cont:
            if all_tactics_cleared and target_not_met:
                remaining_tax = co.tax_target - co.current_collected_tax
                res_t = ResidualTactic(remaining_tax)
                with st.container(border=True):
                    st.markdown(f"**{res_t.name}** (`공통`, `단순 오류`, `공통`)")
                    st.markdown(f"*{res_t.description}*")
                    st.progress(
                        min(1.0, co.current_collected_tax/co.tax_target if co.tax_target > 0 else 1.0),
                        text=f"남은 추징 목표: {remaining_tax:,}억원"
                    )
                    if is_sel and st.session_state.selected_card_index < len(st.session_state.player_hand):
                        if st.button(f"🎯 **{res_t.name}** 공격", key=f"attack_residual", use_container_width=True, type="primary"):
                            execute_attack(st.session_state.selected_card_index, len(co.tactics))
            elif all_tactics_cleared and not target_not_met:
                st.success("모든 혐의 적발 완료! 목표 세액 달성!")
            elif not co.tactics:
                st.write("(조사할 특정 혐의 없음)")
            else:
                for i, t in enumerate(co.tactics):
                    cleared = getattr(t, 'is_cleared', False)
                    with st.container(border=True):
                        t_types_str = ', '.join(get_enum_values(t.tax_type))
                        method_val = safe_get_enum_value(t.method_type, "메소드 오류")
                        category_val = safe_get_enum_value(t.tactic_category, "카테고리 오류")

                        st.markdown(f"**{t.name}** (`{t_types_str}`/`{method_val}`/`{category_val}`)\n*{t.description}*")
                        prog_txt = f"✅ 완료: {t.total_amount:,}억" if cleared else f"적발: {t.exposed_amount:,}/{t.total_amount:,}억"
                        st.progress(
                            1.0 if cleared else (min(1.0, t.exposed_amount/t.total_amount) if t.total_amount > 0 else 1.0),
                            text=prog_txt
                        )
                        
                        if is_sel and not cleared:
                            if st.session_state.selected_card_index < len(st.session_state.player_hand):
                                card = st.session_state.player_hand[st.session_state.selected_card_index]
                                
                                card_tax_values = get_enum_values(card.tax_type)
                                tactic_tax_values = get_enum_values(t.tax_type)
                                is_tax = (TaxType.COMMON.value in card_tax_values) or any(ttv in card_tax_values for ttv in tactic_tax_values)
                                
                                card_cat_values = get_enum_values(card.attack_category)
                                tactic_cat_value = safe_get_enum_value(t.tactic_category)
                                is_cat = (AttackCategory.COMMON.value in card_cat_values) or (tactic_cat_value in card_cat_values)

                                label, type, help = f"🎯 **{t.name}** 공격", "primary", "클릭하여 공격!"
                                
                                if card.special_bonus and card.special_bonus.get('target_method') == t.method_type:
                                    label = f"💥 [특효!] **{t.name}** 공격"
                                    help = f"클릭! ({card.special_bonus.get('bonus_desc')})"
                                
                                disabled = False
                                if not is_tax:
                                    label, type, help, disabled = f"⚠️ (세목 불일치!)", "secondary", f"세목 불일치! '{', '.join(card_tax_values)}' 카드는 '{', '.join(tactic_tax_values)}' 혐의에 사용 불가.", True
                                elif not is_cat:
                                    label, type, help, disabled = f"⚠️ (유형 불일치!)", "secondary", f"유형 불일치! '{', '.join(card_cat_values)}' 카드는 '{tactic_cat_value}' 혐의에 사용 불가.", True
                                
                                if st.button(label, key=f"attack_{i}", use_container_width=True, type=type, disabled=disabled, help=help):
                                    execute_attack(st.session_state.selected_card_index, i)
    
    with col_log:
        if st.session_state.get('hit_effect_player', False):
            st.error("💔 팀 현황 (피격!)")
        else:
            st.subheader("❤️ 팀 현황")
        
        c1, c2 = st.columns(2)
        c1.metric("팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}")
        c2.metric("현재 집중력", f"{st.session_state.player_focus_current}/{st.session_state.player_focus_max}")
        
        if st.session_state.get('cost_reduction_active', False):
            st.info("✨ [실무 지휘] 다음 카드 비용 -1")

        st.subheader("📋 조사 기록 (로그)")
        log_cont = st.container(height=300, border=True)
        for log in st.session_state.battle_log:
            log_cont.markdown(log)
        
        st.markdown("---")
        st.subheader("🕹️ 행동")

        if st.session_state.get("selected_card_index") is not None:
            st.button("❌ 공격 취소", on_click=cancel_card_selection, use_container_width=True, type="secondary")
        else:
            act_cols = st.columns(2)
            act_cols[0].button("➡️ 턴 종료", on_click=end_player_turn, use_container_width=True, type="primary")
            with act_cols[1]:
                c1, c2 = st.columns(2)
                with c1:
                    st.button("⚡ 자동", on_click=execute_auto_attack, use_container_width=True, type="secondary", 
                             help="[❤️-5, 💥-25% 페널티] 가장 강력한 카드로 자동 공격합니다.")

        with st.expander("💡 특별 지시 (대기업 행동)"):
            st.button("과세 논리 개발 (❤️ 현재 체력 50% 소모)", on_click=develop_tax_logic, use_container_width=True, type="primary",
                     help="현재 체력의 절반을 소모하여, 남은 혐의에 가장 유효하고 강력한 공격 카드 1장을 즉시 손패로 가져옵니다.")

    with col_hand:
        st.subheader(f"🃏 손패 ({len(st.session_state.player_hand)})")

        hand_container = st.container(height=650)

        with hand_container:
            if not st.session_state.player_hand:
                st.write("(손패 없음)")

            for i, card in enumerate(st.session_state.player_hand):
                if i >= len(st.session_state.player_hand):
                    continue
                
                cost = calculate_card_cost(card)
                afford = st.session_state.player_focus_current >= cost
                color = "blue" if afford else "red"
                selected = (st.session_state.get("selected_card_index") == i)

                with st.container(border=True):
                    selected_str = ":blue[** (선택됨)**]" if selected else ""
                    title_line = f":{color}[**{cost}🧠**] **{card.name}**{selected_str}"

                    info_parts = []
                    if card.base_damage > 0:
                        info_parts.append(f"💥{card.base_damage}억")
                    if card.special_bonus:
                        info_parts.append(f"🔥{card.special_bonus.get('bonus_desc')}")
                    if not info_parts:
                        if card.special_effect and card.special_effect.get("type") == "draw":
                            info_parts.append(f"✨드로우 +{card.special_effect.get('value')}")
                        elif card.special_effect and card.special_effect.get("type") == "search_draw":
                            info_parts.append("🔍카드 서치")

                    info_line = " | ".join(info_parts)

                    if info_line:
                        st.markdown(f"{title_line} <small>({info_line})</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(title_line)

                    btn_label = "선택" if (card.base_damage > 0) else "사용"
                    if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]:
                        btn_label = "사용"

                    disabled = not afford
                    c_types_values = get_enum_values(card.tax_type)
                    c_cats_values = get_enum_values(card.attack_category)
                    tooltip = f"[{card.name}] {card.description}\n세목:{'`,`'.join(c_types_values)} | 유형:{'`,`'.join(c_cats_values)}"

                    if not afford:
                        tooltip = f"집중력 부족! ({cost})"

                    if st.button(btn_label, key=f"play_{i}", use_container_width=True, disabled=disabled, help=tooltip):
                        select_card_to_play(i)

def show_reward_bonus_screen():
    """보너스 보상 화면"""
    st.header("✨ 추가 보상 발견!")
    st.markdown("---")

    reward_artifact = st.session_state.get('bonus_reward_artifact', None)
    reward_member = st.session_state.get('bonus_reward_member', None)

    if reward_artifact:
        st.subheader("🎁 새로운 조사 도구를 발견했습니다!")
        with st.container(border=True):
            st.markdown(f"**{reward_artifact.name}**")
            st.write(reward_artifact.description)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 획득하기", use_container_width=True, type="primary"):
                st.session_state.player_artifacts.append(reward_artifact)
                log_message(f"🎁 조사 도구 '{reward_artifact.name}' 정식 획득!", "success")
                st.toast(f"획득: {reward_artifact.name}", icon="🧰")
                recalculate_team_stats()
                st.session_state.bonus_reward_artifact = None
                st.session_state.game_state = "REWARD"
                st.rerun()
        with col2:
            if st.button("👎 포기하기", use_container_width=True):
                log_message(f"🗑️ 조사 도구 '{reward_artifact.name}' 획득 포기.", "warning")
                st.session_state.bonus_reward_artifact = None
                st.session_state.game_state = "REWARD"
                st.rerun()

    elif reward_member:
        st.subheader("👥 새로운 팀원이 합류를 기다립니다!")
        with st.container(border=True):
            st.markdown(f"**{reward_member.name}**")
            st.write(f"({reward_member.description})")
            st.info(f"**{reward_member.ability_name}**: {reward_member.ability_desc}")
            st.caption(f"HP: {reward_member.hp}, 집중력: {reward_member.focus}, 분석:{reward_member.analysis}, 설득:{reward_member.persuasion}, 증거:{reward_member.evidence}, 데이터:{reward_member.data}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 영입하기", use_container_width=True, type="primary"):
                st.session_state.player_team.append(reward_member)
                log_message(f"👥 '{reward_member.name}' 조사관 정식 합류!", "success")
                st.toast(f"합류: {reward_member.name}", icon="👨‍💼")
                recalculate_team_stats()
                st.session_state.bonus_reward_member = None
                st.session_state.game_state = "REWARD"
                st.rerun()
        with col2:
            if st.button("👎 거절하기", use_container_width=True):
                log_message(f"🚶 '{reward_member.name}' 조사관 영입 거절.", "warning")
                st.session_state.bonus_reward_member = None
                st.session_state.game_state = "REWARD"
                st.rerun()
    else:
        st.warning("표시할 추가 보상이 없습니다. 카드 선택 화면으로 이동합니다.")
        st.session_state.game_state = "REWARD"
        st.rerun()

def show_reward_screen():
    """보상 화면"""
    # 아직 처리 안 된 보너스 보상이 있으면 REWARD_BONUS로 리다이렉트
    if st.session_state.get('bonus_reward_artifact') or st.session_state.get('bonus_reward_member'):
        st.session_state.game_state = "REWARD_BONUS"
        st.rerun()
        return

    st.header("🎉 조사 승리!")
    st.balloons()
    
    co = st.session_state.current_battle_company
    st.success(f"**{co.name}** 조사 완료. 총 {co.current_collected_tax:,}억원 추징.")
    
    # 조사 보고서
    with st.expander("📋 조사 보고서 보기"):
        report = EducationalSystem.generate_battle_report(co, st.session_state.battle_stats)
        
        st.subheader("📊 조사 효율성")
        c1, c2, c3 = st.columns(3)
        c1.metric("턴당 추징액", f"{report['efficiency']['damage_per_turn']:.1f}억원")
        c2.metric("턴당 카드 사용", f"{report['efficiency']['cards_per_turn']:.1f}장")
        c3.metric("목표 달성률", f"{report['efficiency']['target_achievement']:.1f}%")
        
        if report['suggestions']:
            st.subheader("💡 개선 제안")
            for suggestion in report['suggestions']:
                st.info(suggestion)
    
    st.markdown("---")

    if st.session_state.current_stage_level >= len(st.session_state.company_order) - 1:
        st.session_state.game_state = "GAME_CLEAR"
        st.rerun()
        return

    st.subheader("🎁 획득할 카드 1장 선택")
    
    if 'reward_cards' not in st.session_state or not st.session_state.reward_cards:
        pool = [c for c in LOGIC_CARD_DB.values() 
               if not (c.cost == 0 and c.special_effect and c.special_effect.get("type") == "draw")]
        opts = []
        
        has_cap = any(t.method_type == MethodType.CAPITAL_TX for t in co.tactics)
        if has_cap:
            cap_cards = [c for c in pool if AttackCategory.CAPITAL in c.attack_category and c not in opts]
            if cap_cards:
                opts.append(random.choice(cap_cards))
                st.toast("ℹ️ [보상 가중치] '자본' 카드 1장 포함!")
        
        remain = [c for c in pool if c not in opts]
        num_add = 3 - len(opts)
        
        if len(remain) < num_add:
            opts.extend(random.sample(remain, len(remain)))
        else:
            opts.extend(random.sample(remain, num_add))
        
        while len(opts) < 3 and len(pool) > 0:
            add = random.choice(pool)
            if add not in opts or len(pool) < 3:
                opts.append(add)
        
        st.session_state.reward_cards = opts

    cols = st.columns(len(st.session_state.reward_cards))
    for i, card in enumerate(st.session_state.reward_cards):
        with cols[i]:
            with st.container(border=True):
                types_values = get_enum_values(card.tax_type)
                cats_values = get_enum_values(card.attack_category)
                st.markdown(f"**{card.name}**|비용:{card.cost}🧠")
                st.caption(f"세목:`{'`,`'.join(types_values)}`|유형:`{'`,`'.join(cats_values)}`")
                st.markdown(card.description)
                
                if card.base_damage > 0:
                    st.info(f"**기본 적출액:** {card.base_damage} 억원")
                elif card.special_effect and card.special_effect.get("type") == "draw":
                    st.info(f"**드로우:** +{card.special_effect.get('value', 0)}")
                
                if card.special_bonus:
                    st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")

                if st.button(f"선택: {card.name}", key=f"reward_{i}", use_container_width=True, type="primary"):
                    go_to_next_stage(add_card=card)

    st.markdown("---")
    st.button("카드 획득 안 함 (다음 스테이지로)", on_click=go_to_next_stage, type="secondary", use_container_width=True)

def show_game_over_screen():
    """게임 오버 화면"""
    st.header("... 조사 중단 ...")
    st.error("팀 체력 소진.")
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax:,} 억원")
    st.metric("진행 스테이지", f"📍 {st.session_state.current_stage_level + 1} / 4")
    st.image("https://images.unsplash.com/photo-1518340101438-1d16873c3a88?q=80&w=1740&auto=format&fit=crop", 
             caption="조사에 지친 조사관들...", width=400)
    st.button("다시 도전", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), type="primary", use_container_width=True)

def show_game_clear_screen():
    """게임 클리어 화면"""
    st.header("🎉 조사 완료!")
    st.balloons()
    st.success(f"축하합니다! 4단계의 조사를 모두 성공적으로 완료했습니다.")
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax:,} 억원")
    st.metric("진행 스테이지", f"📍 4 / 4")
    st.image("https://images.unsplash.com/photo-1517048676732-d65bc937f952?q=80&w=1740&auto=format&fit=crop", 
             caption="성공적으로 임무를 완수한 조사팀.", width=400)
    st.button("🏆 메인 메뉴로 돌아가기", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), type="primary", use_container_width=True)

def show_player_status_sidebar():
    """사이드바"""
    with st.sidebar:
        st.title("👨‍💼 조사팀 현황")
        st.metric("💰 총 추징 세액", f"{st.session_state.total_collected_tax:,} 억원")
        st.metric("❤️ 현재 팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}")

        st.markdown("---")
        with st.expander("📊 팀 스탯", expanded=False):
            stats = st.session_state.team_stats
            st.markdown(f"- 분석력: {stats['analysis']}\n- 설득력: {stats['persuasion']}\n- 증거력: {stats['evidence']}\n- 데이터: {stats['data']}")

        st.subheader(f"👥 팀원 ({len(st.session_state.player_team)}명)")
        for m in st.session_state.player_team:
            with st.expander(f"**{m.name}**"):
                st.markdown(f"HP:{m.hp}/{m.max_hp}, Focus:{m.focus}\n**{m.ability_name}**: {m.ability_desc}\n({m.description})")

        st.markdown("---")
        total = len(st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand)
        st.subheader(f"📚 보유 덱 ({total}장)")
        
        with st.expander("덱 구성 보기"):
            deck = st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand
            counts = {}
            for card in deck:
                counts[card.name] = counts.get(card.name, 0) + 1
            for name in sorted(counts.keys()):
                st.write(f"- {name} x {counts[name]}")
        
        if st.session_state.game_state == "BATTLE":
            with st.expander("🗑️ 버린 덱 보기"):
                discard_counts = {name: 0 for name in counts}
                for card in st.session_state.player_discard:
                    discard_counts[card.name] = discard_counts.get(card.name, 0) + 1
                if not any(v > 0 for v in discard_counts.values()):
                    st.write("(버린 카드 없음)")
                else:
                    for n, c in sorted(discard_counts.items()):
                        if c > 0:
                            st.write(f"- {n} x {c}")
        
        st.markdown("---")
        st.subheader("🧰 보유 도구")
        if not st.session_state.player_artifacts:
            st.write("(없음)")
        else:
            for art in st.session_state.player_artifacts:
                st.success(f"- {art.name}: {art.description}")
        
        st.markdown("---")
        st.button("게임 포기 (메인 메뉴)", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), use_container_width=True)

# --- 5. 메인 실행 로직 ---

def main():
    """메인 함수"""
    st.set_page_config(page_title="세무조사 덱빌딩", layout="wide", initial_sidebar_state="expanded")
    
    # 게임 상태 초기화
    GameState.initialize()

    running = ["MAP", "BATTLE", "REWARD", "REWARD_BONUS"]

    if st.session_state.game_state in running and 'player_team' not in st.session_state:
        st.toast("⚠️ 세션 만료, 메인 메뉴로.")
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()
        return

    pages = {
        "MAIN_MENU": show_main_menu,
        "GAME_SETUP_DRAFT": show_setup_draft_screen,
        "MAP": show_map_screen,
        "BATTLE": show_battle_screen,
        "REWARD": show_reward_screen,
        "REWARD_BONUS": show_reward_bonus_screen,
        "GAME_OVER": show_game_over_screen,
        "GAME_CLEAR": show_game_clear_screen
    }

    if st.session_state.game_state in pages:
        pages[st.session_state.game_state]()
    else:
        st.error("알 수 없는 게임 상태입니다. 메인 메뉴로 돌아갑니다.")
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()

    if st.session_state.game_state not in ["MAIN_MENU", "GAME_OVER", "GAME_SETUP_DRAFT", "GAME_CLEAR"] and 'player_team' in st.session_state:
        show_player_status_sidebar()

if __name__ == "__main__":
    main()


