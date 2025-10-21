import streamlit as st
import random
import copy
from enum import Enum
import math
import time # 자동공격 버튼용 (실제로는 HP로 대체)

# --- 0. Enum(열거형) 정의 ---
class TaxType(str, Enum): CORP = "법인세"; VAT = "부가세"; COMMON = "공통"
class AttackCategory(str, Enum): COST = "비용"; REVENUE = "수익"; CAPITAL = "자본"; COMMON = "공통"
class MethodType(str, Enum): INTENTIONAL = "고의적 누락"; ERROR = "단순 오류"; CAPITAL_TX = "자본 거래"

# --- 헬퍼 함수 (SyntaxError 수정) ---
def format_krw(amount):
    if amount is None: return "N/A"
    try:
        if abs(amount) >= 1_000_000: return f"{amount / 1_000_000:,.1f}조원"
        elif abs(amount) >= 10_000: return f"{amount / 10_000:,.0f}억원"
        elif abs(amount) >= 100: return f"{amount / 100:,.0f}억원"
        else: return f"{amount:,.0f}백만원"
    except Exception: return f"{amount} (Format Error)"

# --- 1. 기본 데이터 구조 ---
class Card:
    def __init__(self, name, description, cost): self.name = name; self.description = description; self.cost = cost;

class TaxManCard(Card):
    # [수정] hp 기본값 20% 감소 (생성자에서 처리)
    def __init__(self, name, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost);
        nerfed_hp = int(hp * 0.8) # 20% 너프
        self.hp=nerfed_hp; self.max_hp=nerfed_hp;
        self.focus=focus; self.analysis=analysis; self.persuasion=persuasion; self.evidence=evidence; self.data=data; self.ability_name=ability_name; self.ability_desc=ability_desc;

class LogicCard(Card):
    # [수정] cost 기본값 +1 증가 (생성자에서 처리)
    def __init__(self, name, description, cost, base_damage, tax_type: list[TaxType], attack_category: list[AttackCategory], text, special_effect=None, special_bonus=None):
        super().__init__(name, description, max(0, cost + 1)); # 비용 +1 증가 (최소 0)
        self.base_damage=base_damage; self.tax_type=tax_type; self.attack_category=attack_category; self.text=text; self.special_effect=special_effect; self.special_bonus=special_bonus;

class EvasionTactic:
    def __init__(self, name, description, total_amount, tax_type: TaxType | list[TaxType], method_type: MethodType, tactic_category: AttackCategory):
        self.name=name; self.description=description; self.total_amount=total_amount; self.exposed_amount=0; self.tax_type=tax_type; self.method_type=method_type; self.tactic_category=tactic_category; self.is_cleared=False;
class ResidualTactic(EvasionTactic): # 잔여 혐의 클래스
     def __init__(self, remaining_tax):
          super().__init__(name="[잔여 혐의 조사]",
                           description=f"특정 혐의를 모두 적발했습니다. 남은 목표 세액 {remaining_tax:,}억원을 마저 추징합니다.",
                           total_amount=remaining_tax,
                           tax_type=[TaxType.COMMON],
                           method_type=MethodType.ERROR,
                           tactic_category=AttackCategory.COMMON)
     @property
     def is_cleared(self): return False
     @is_cleared.setter
     def is_cleared(self, value): pass
class Company:
    # [수정] team_hp_damage 20% 증가 (생성자에서 처리)
    def __init__(self, name, size, description, real_case_desc, revenue, operating_income, tax_target, team_hp_damage, tactics, defense_actions):
        self.name=name; self.size=size; self.description=description; self.real_case_desc=real_case_desc; self.revenue=revenue; self.operating_income=operating_income; self.tax_target=tax_target;
        # 20% 증가 (올림)
        buffed_damage = (math.ceil(team_hp_damage[0] * 1.2), math.ceil(team_hp_damage[1] * 1.2))
        self.team_hp_damage=buffed_damage;
        self.current_collected_tax=0; self.tactics=tactics; self.defense_actions=defense_actions;
class Artifact:
    def __init__(self, name, description, effect): self.name=name; self.description=description; self.effect=effect;

# --- 2. 게임 데이터베이스 (DB) ---
# [수정] 모든 TaxManCard의 hp는 생성자에서 20% 감소됨
TAX_MAN_DB = {
    "lim": TaxManCard(name="임향수", description="조사통의 대부. 대기업 비자금, 불법 증여 조사 지휘 경험 풍부.", cost=0, hp=120, focus=3, analysis=10, persuasion=10, evidence=10, data=10, ability_name="[기획 조사]", ability_desc="매 턴 집중력+1. 분석/데이터 스탯 비례 비용/자본 카드 피해량 증가."),
    "han": TaxManCard(name="한중후", description="국제조세 전문가. OECD 파견 경험으로 국제 공조 및 BEPS 이해 깊음.", cost=0, hp=80, focus=2, analysis=9, persuasion=6, evidence=8, data=9, ability_name="[역외탈세 추적]", ability_desc="'외국계' 기업 또는 '자본 거래' 혐의 공격 시 최종 피해량 +30%."),
    "baek": TaxManCard(name="백용호", description="세제 전문가. TIS, NTIS 등 과학세정 인프라 구축 경험.", cost=0, hp=90, focus=2, analysis=7, persuasion=10, evidence=9, data=7, ability_name="[TIS 분석]", ability_desc="'금융거래 분석', '빅데이터 분석' 등 데이터 관련 카드 비용 -1."),
    "seo": TaxManCard(name="서영택", description="조사 전문가. 변칙 상속/증여 조사를 강력 지휘. 대기업 조사 정통.", cost=0, hp=100, focus=2, analysis=8, persuasion=9, evidence=8, data=7, ability_name="[대기업 저격]", ability_desc="'대기업', '외국계' 기업의 '법인세' 혐의 카드 공격 시 최종 피해량 +25%."),
    "kim_dj": TaxManCard(name="김대조", description="세정 운영 전문가. 데이터 기반 대규모 조사 경험.", cost=0, hp=90, focus=2, analysis=10, persuasion=7, evidence=7, data=10, ability_name="[부동산 투기 조사]", ability_desc="팀 '데이터' 스탯 50+ 시, 턴 시작 시 '금융거래 분석' 카드 1장 생성."),
    "lee_hd": TaxManCard(name="이현동", description="강력한 추진력의 조사통. 지하경제 양성화 및 역외탈세 추적 의지 강함.", cost=0, hp=100, focus=3, analysis=7, persuasion=8, evidence=10, data=8, ability_name="[지하경제 양성화]", ability_desc="'고의적 누락(Intentional)' 혐의 공격의 최종 피해량 +20%."),
    "kim": TaxManCard(name="김철주", description="현장 전문가. 서울청 조사0국 '지하경제 양성화' 관련 조사 다수 수행.", cost=0, hp=110, focus=2, analysis=6, persuasion=8, evidence=9, data=5, ability_name="[압수수색]", ability_desc="'현장 압수수색' 카드 사용 시 15% 확률로 '결정적 증거' 추가 획득."),
    "oh": TaxManCard(name="전팔성", description="[가상] 데이터 전문가. TIS 초기 멤버로 시스템 이해도 높음. 신종 거래 분석 능함.", cost=0, hp=110, focus=2, analysis=7, persuasion=6, evidence=7, data=8, ability_name="[데이터 마이닝]", ability_desc="기본 적출액 70억 이상 '데이터' 관련 카드(자금출처조사 등) 피해량 +15."),
    "jo": TaxManCard(name="조용규", description="세법 이론가. 교육원 교수 경험. 법리 해석과 판례 분석 뛰어남.", cost=0, hp=80, focus=3, analysis=9, persuasion=7, evidence=6, data=7, ability_name="[세법 교본]", ability_desc="'판례 제시', '법령 재검토' 카드의 효과(피해량/드로우) 2배 적용."),
    "park": TaxManCard(name="박조연", description="[가상] 세법 신동. 세무사/CPA 동시 합격 특채. 날카로운 법리 검토 능력.", cost=0, hp=70, focus=3, analysis=7, persuasion=5, evidence=6, data=7, ability_name="[법리 검토]", ability_desc="턴마다 처음 사용하는 '분석' 또는 '설득' 유형 카드의 비용 -1."),
    "lee": TaxManCard(name="이찰수", description="[가상] 7급 공채 신입. 열정 넘치나 경험 부족. 기본기 충실.", cost=0, hp=80, focus=2, analysis=5, persuasion=5, evidence=5, data=5, ability_name="[기본기]", ability_desc="'기본 경비 적정성 검토', '단순 경비 처리 오류 지적' 카드 피해량 +8."),
    "ahn_wg": TaxManCard(name="안원규", description="특수 조사의 귀재. 서울청 조사0국 등에서 대기업 비자금 등 특수 조사 경험 풍부.", cost=0, hp=110, focus=2, analysis=8, persuasion=5, evidence=10, data=6, ability_name="[특수 조사]", ability_desc="'현장 압수수색', '차명계좌 추적' 카드 비용 -1 (최소 0)."),
    "yoo_jj": TaxManCard(name="유재전", description="관리자. 서울청 조사0국 대기업 정기 조사 및 상속/증여세 조사 담당. 분석/설득 강점.", cost=0, hp=100, focus=2, analysis=8, persuasion=7, evidence=7, data=7, ability_name="[정기 조사 전문]", ability_desc="'단순 오류(Error)' 혐의 공격 시, 팀 '설득' 스탯 10당 피해량 +1."),
    "kim_th": TaxManCard(name="김태후", description="관리자. 중부청 조사0국 대기업/중견기업 심층 기획 및 국제거래 조사 담당. 증거 확보/데이터 분석 탁월.", cost=0, hp=105, focus=2, analysis=9, persuasion=5, evidence=9, data=8, ability_name="[심층 기획 조사]", ability_desc="'자본 거래(Capital Tx)' 혐의 공격 시, 팀 '증거' 스탯의 10%만큼 추가 피해."),
    "jeon_j": TaxManCard(name="전준", description="실무 과장. 중부청 조사0국. 조사 현장 지휘 경험 풍부, 팀원 능력 활용 능숙.", cost=0, hp=85, focus=3, analysis=7, persuasion=6, evidence=6, data=6, ability_name="[실무 지휘]", ability_desc="턴 시작 시, **팀**의 다음 카드 사용 비용 -1.")
}

# [수정] 모든 LogicCard의 cost는 생성자에서 +1 증가됨
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
# --- [신규] 2개의 조사 도구 추가 ---
ARTIFACT_DB = {
    "coffee": Artifact(name="☕ 믹스 커피", description="턴 시작 시 집중력 +1.", effect={"type": "on_turn_start", "value": 1, "subtype": "focus"}),
    "forensic": Artifact(name="💻 포렌식 장비", description="팀 '증거(Evidence)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_evidence"}),
    "plan": Artifact(name="📜 조사계획서", description="첫 턴 카드 +1장.", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
    "recorder": Artifact(name="🎤 녹음기", description="팀 '설득(Persuasion)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_persuasion"}),
    "book": Artifact(name="📖 오래된 법전", description="'판례 제시', '법령 재검토' 비용 -1.", effect={"type": "on_cost_calculate", "value": -1, "target_cards": ["판례 제시", "법령 재검토"]}),
    # --- 신규 도구 2개 ---
    "report": Artifact(name="📊 분기 보고서", description="팀 '분석(Analysis)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_analysis"}),
    "badge": Artifact(name="🎖️ 우수 조사관 배지", description="첫 턴 카드 +1장. (조사계획서와 중첩 가능)", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
}
# --- [수정] 기업 이름 변경 및 team_hp_damage는 생성자에서 20% 증가됨 ---
COMPANY_DB = [
    # --- C Group (Easy, 9-11th) ---
    Company(
        name="(주)가나푸드", size="소규모", revenue=8000, operating_income=800, tax_target=10, team_hp_damage=(5, 12),
        description="인기 **SNS 인플루언서**가 운영하는 **온라인 쇼핑몰**(식품 유통). 대표는 **고가 외제차**, **명품** 과시.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
    Company(
        # [수정] 이름 변경: 쿠팡 -> 코팡
        name="㈜코팡 (Kopang)", size="중견기업", revenue=300000, operating_income=10000, tax_target=50, team_hp_damage=(10, 20),
        description="빠른 배송으로 유명한 **E-커머스 플랫폼**. **쿠폰 발행**, **포인트 적립** 등 프로모션 비용이 막대함.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
    Company(
        # [수정] 이름 변경: 넥산 -> 넥선
        name="㈜넥선 (Nexun)", size="중견기업", revenue=200000, operating_income=15000, tax_target=100, team_hp_damage=(15, 30),
        description="최근 급성장한 **게임/IT 기업**. **R&D 투자**가 많고 임직원 **스톡옵션** 부여가 잦습니다.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),

    # --- B Group (Medium, 6-8th) ---
    Company(
        name="(주)한늠석유 (자료상)", size="중견기업", revenue=70000, operating_income=-800, tax_target=150, team_hp_damage=(20, 35),
        description="전형적인 '**자료상**' 의심 업체. **유가보조금 부정수급** 및 **허위 세금계산서** 발행 전력.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
    Company(
        name="(주)대롬건설 (Daelom E&C)", size="중견기업", revenue=500000, operating_income=25000, tax_target=200, team_hp_damage=(20, 30),
        description="다수의 **관급 공사** 수주 이력이 있는 **중견 건설사**. **하도급** 거래가 복잡함.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
    Company(
        name="(주)한모약품 (Hanmo Pharm)", size="중견기업", revenue=400000, operating_income=30000, tax_target=300, team_hp_damage=(20, 35),
        description="**신약 개발**에 막대한 자금을 투자하는 **제약/바이오** 기업. **기술 수출** 실적 보유.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),

    # --- A Group (Hard, 3-5th) ---
    Company(
        # [수정] 이름 변경: 로때 -> 로떼
        name="(주)로떼 (Lottee)", size="대기업", revenue=30_000_000, operating_income=1_000_000, tax_target=800, team_hp_damage=(18, 30),
        description="**유통, 화학, 건설** 등 다수 계열사 보유 **대기업 그룹**. **순환출자** 구조 및 **경영권 분쟁** 이력.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
    Company(
        # [수정] 이름 변경: 삼송 -> 삼숭
        name="㈜삼숭물산 (Samsyoong)", size="대기업", revenue=60_000_000, operating_income=2_500_000, tax_target=1200, team_hp_damage=(20, 40),
        description="국내 굴지 **대기업 그룹**의 핵심 계열사. **경영권 승계**, **신사업 투자**, **해외 M&A** 활발.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
    Company(
        name="(주)씨엔해운 (C&N)", size="대기업", revenue=12_000_000, operating_income=600_000, tax_target=1600, team_hp_damage=(25, 45),
        description="'**해운 재벌**'로 불리는 오너 운영. **조세피난처 SPC** 활용 및 **선박금융** 관련 복잡한 거래 구조.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),

    # --- S Group (Global, 1-2nd) ---
    Company(
        # [수정] 이름 변경: 구골 -> 구굴
        name="구굴 코리아(유) (Googul)", size="글로벌 기업", revenue=3_000_000, operating_income=400_000, tax_target=1000, team_hp_damage=(18, 35),
        description="글로벌 **IT 공룡**의 한국 지사. **디지털 광고**, **클라우드** 사업 영위.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
    Company(
        # [수정] 이름 변경: 아마존 -> 아메존
        name="아메존 코리아 (Amejon)", size="글로벌 기업", revenue=20_000_000, operating_income=500_000, tax_target=1800, team_hp_damage=(30, 50),
        description="세계 최대 **E-커머스** 및 **클라우드 서비스** 기업. 국내 **물류센터** 운영 및 **AWS** 사업 활발.",
        real_case_desc="...", tactics=[...], defense_actions=["..."]
    ),
]


# --- 3. 게임 상태 초기화 및 관리 ---
def initialize_game(chosen_lead: TaxManCard, chosen_artifact: Artifact):
    seed = st.session_state.get('seed', 0); random.seed(seed if seed != 0 else None)
    if seed != 0: st.toast(f"ℹ️ RNG 시드 {seed} 고정됨.")
    team_members = [chosen_lead]; all_mem = list(TAX_MAN_DB.values());
    remain = [m for m in all_mem if m.name != chosen_lead.name];
    team_members.extend(random.sample(remain, min(2, len(remain)))); st.session_state.player_team = team_members

    start_deck = [
        LOGIC_CARD_DB["basic_01"], LOGIC_CARD_DB["basic_01"],
        LOGIC_CARD_DB["basic_02"],
        LOGIC_CARD_DB["b_tier_04"],
        LOGIC_CARD_DB["c_tier_02"], LOGIC_CARD_DB["c_tier_02"],
        LOGIC_CARD_DB["c_tier_01"], LOGIC_CARD_DB["c_tier_01"], LOGIC_CARD_DB["c_tier_01"],
        LOGIC_CARD_DB["c_tier_01"], LOGIC_CARD_DB["c_tier_01"]
    ] # 총 11장

    st.session_state.player_deck = random.sample(start_deck, len(start_deck)); st.session_state.player_hand=[]; st.session_state.player_discard=[]
    st.session_state.player_artifacts=[chosen_artifact]

    # [수정] 팀 스탯 계산 로직 함수화 (팀원 추가 시 재사용 위함)
    recalculate_team_stats()

    all_companies = sorted(COMPANY_DB, key=lambda x: x.tax_target)
    group_c = all_companies[0:3]
    group_b = all_companies[3:6]
    group_a = all_companies[6:9]
    group_s = all_companies[9:11]

    stage1 = random.choice(group_c)
    stage2 = random.choice(group_b)
    stage3 = random.choice(group_a)
    stage4 = random.choice(group_s)

    st.session_state.company_order = [stage1, stage2, stage3, stage4]

    st.session_state.current_battle_company=None; st.session_state.battle_log=[]; st.session_state.selected_card_index=None; st.session_state.bonus_draw=0;
    st.session_state.game_state="MAP"; st.session_state.current_stage_level=0; st.session_state.total_collected_tax=0

# --- [신규] 팀 스탯 재계산 함수 ---
def recalculate_team_stats():
    team_members = st.session_state.player_team
    st.session_state.team_max_hp = sum(m.hp for m in team_members)
    # 현재 체력도 최대 체력을 넘지 않도록 조정
    if 'team_hp' in st.session_state:
        st.session_state.team_hp = min(st.session_state.team_hp, st.session_state.team_max_hp)
    else:
        st.session_state.team_hp = st.session_state.team_max_hp

    st.session_state.player_focus_max = sum(m.focus for m in team_members)
    # 현재 집중력도 최대 집중력을 넘지 않도록 조정
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
    # 유물에 의한 스탯 보너스 재적용
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_battle_start":
            if art.effect["subtype"] == "stat_evidence": st.session_state.team_stats["evidence"] += art.effect["value"]
            elif art.effect["subtype"] == "stat_persuasion": st.session_state.team_stats["persuasion"] += art.effect["value"]
            elif art.effect["subtype"] == "stat_analysis": st.session_state.team_stats["analysis"] += art.effect["value"] # 분기 보고서


# --- 4. 게임 로직 함수 ---

def start_player_turn():
    st.session_state.hit_effect_player = False

    # [수정] 최대 집중력은 매 턴 시작 시 팀원 기준으로 재계산
    st.session_state.player_focus_max = sum(m.focus for m in st.session_state.player_team)
    st.session_state.player_focus_current = st.session_state.player_focus_max # 현재 집중력은 최대로 회복

    if "임향수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current+=1
        log_message("✨ [기획 조사] 집중력 +1!", "info")
    for art in st.session_state.player_artifacts:
        if art.effect["type"]=="on_turn_start" and art.effect["subtype"]=="focus":
            st.session_state.player_focus_current+=art.effect["value"]
            log_message(f"✨ {art.name} 집중력 +{art.effect['value']}!", "info")
    # 최대치 초과 방지
    st.session_state.player_focus_current = min(st.session_state.player_focus_current, st.session_state.player_focus_max + 10) # 임시 최대치 +10 버퍼

    if "김대조" in [m.name for m in st.session_state.player_team] and st.session_state.team_stats["data"]>=50 and not st.session_state.get('kim_dj_effect_used', False):
        new=copy.deepcopy(LOGIC_CARD_DB["b_tier_01"]); new.just_created=True; st.session_state.player_hand.append(new);
        log_message("✨ [부동산 조사] '금융거래 분석' 1장 획득!", "info"); st.session_state.kim_dj_effect_used=True
    st.session_state.cost_reduction_active = "전준" in [m.name for m in st.session_state.player_team];
    if st.session_state.cost_reduction_active:
        log_message("✨ [실무 지휘] 다음 카드 비용 -1!", "info")

    # 첫 턴 드로우 보너스 계산 (중첩 가능)
    st.session_state.bonus_draw = 0
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_battle_start" and art.effect["subtype"] == "draw":
            st.session_state.bonus_draw += art.effect["value"]

    draw_n = 4 + st.session_state.get('bonus_draw', 0)
    if st.session_state.get('bonus_draw', 0)>0:
        log_message(f"✨ 시작 보너스로 카드 {st.session_state.bonus_draw}장 추가 드로우!", "info")
        # bonus_draw는 첫 턴에만 적용되므로 여기서 초기화하지 않음 (start_battle에서 초기화)

    draw_cards(draw_n); check_draw_cards_in_hand(); log_message("--- 플레이어 턴 시작 ---"); st.session_state.turn_first_card_played=True; st.session_state.selected_card_index=None

def draw_cards(num):
    drawn = []
    for _ in range(num):
        if not st.session_state.player_deck:
            if not st.session_state.player_discard: log_message("경고: 더 뽑을 카드 없음!", "error"); break
            log_message("덱 리셔플."); st.session_state.player_deck = random.sample(st.session_state.player_discard, len(st.session_state.player_discard)); st.session_state.player_discard = []
            if not st.session_state.player_deck: log_message("경고: 덱/버린 덱 모두 비었음!", "error"); break
        if not st.session_state.player_deck: log_message("경고: 덱 비었음!", "error"); break
        card = st.session_state.player_deck.pop(); drawn.append(card)
    st.session_state.player_hand.extend(drawn)

def check_draw_cards_in_hand():
    indices = [i for i, c in enumerate(st.session_state.player_hand) if c.cost==0 and c.special_effect and c.special_effect.get("type")=="draw" and not getattr(c, 'just_created', False)]
    indices.reverse(); total_draw=0
    for idx in indices:
        if idx < len(st.session_state.player_hand):
            card = st.session_state.player_hand.pop(idx); st.session_state.player_discard.append(card); val = card.special_effect.get('value', 0); log_message(f"✨ [{card.name}] 효과! 카드 {val}장 뽑기.", "info")
            if "조용규" in [m.name for m in st.session_state.player_team] and card.name=="법령 재검토":
                log_message("✨ [세법 교본] +1장 추가!", "info")
                val*=2
            total_draw += val
        else: log_message(f"경고: 드로우 처리 인덱스 오류 (idx: {idx})", "error")
    for card in st.session_state.player_hand:
        if hasattr(card, 'just_created'): card.just_created=False
    if total_draw > 0: draw_cards(total_draw)

def execute_utility_card(card_index):
    if card_index is None or card_index >= len(st.session_state.player_hand): return
    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); return
    st.session_state.player_focus_current -= cost
    if st.session_state.get('turn_first_card_played', True): st.session_state.turn_first_card_played = False
    effect = card.special_effect.get("type")
    if effect == "search_draw":
        cats = list(set([t.tactic_category for t in st.session_state.current_battle_company.tactics if not t.is_cleared]))
        if not cats: log_message("ℹ️ [빅데이터 분석] 분석할 혐의 없음.", "info")
        else:
            pool=st.session_state.player_deck+st.session_state.player_discard; random.shuffle(pool)
            found = next((c for c in pool if c not in st.session_state.player_hand and c.cost>0 and AttackCategory.COMMON not in c.attack_category and not (c.special_effect and c.special_effect.get("type")=="draw") and any(cat in cats for cat in c.attack_category)), None)
            if found:
                log_message(f"📊 [빅데이터 분석] '{found.name}' 발견!", "success"); new=copy.deepcopy(found); new.just_created=True; st.session_state.player_hand.append(new);
                try: st.session_state.player_deck.remove(found)
                except ValueError:
                    try: st.session_state.player_discard.remove(found)
                    except ValueError: log_message("경고: 빅데이터 카드 제거 오류", "error")
            else: log_message("ℹ️ [빅데이터 분석] 관련 카드 없음...", "info")
    elif effect == "draw":
        val = card.special_effect.get("value", 0); log_message(f"✨ [{card.name}] 효과! 카드 {val}장 드로우!", "info"); draw_cards(val)
    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None
    check_draw_cards_in_hand(); st.rerun()

def select_card_to_play(card_index):
    if 'player_hand' not in st.session_state or card_index >= len(st.session_state.player_hand): st.toast("오류: 유효 카드 아님.", icon="🚨"); return
    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); return
    if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]: execute_utility_card(card_index)
    else: st.session_state.selected_card_index = card_index; st.rerun()

def cancel_card_selection(): st.session_state.selected_card_index = None; st.rerun()

# [수정] 카드 비용 계산 시, 인물 능력(백용호, 박조연, 안원규, 전준)은 +1된 비용 이전에 적용되도록 순서 조정
def calculate_card_cost(card):
    original_cost = card.cost - 1 # 생성자에서 +1 되었으므로 원래 비용으로 복원
    cost = original_cost

    # 인물 능력에 의한 비용 감소 (원래 비용 기준)
    if "백용호" in [m.name for m in st.session_state.player_team] and ('데이터' in card.name or '분석' in card.name or AttackCategory.CAPITAL in card.attack_category):
        cost = max(0, cost - 1)
    is_first = st.session_state.get('turn_first_card_played', True);
    type_match = ('분석' in card.name or '판례' in card.name or '법령' in card.name or AttackCategory.COMMON in card.attack_category)
    if "박조연" in [m.name for m in st.session_state.player_team] and is_first and type_match:
        cost = max(0, cost - 1)
    if "안원규" in [m.name for m in st.session_state.player_team] and card.name in ['현장 압수수색', '차명계좌 추적']:
        cost = max(0, cost - 1)
    if st.session_state.get('cost_reduction_active', False):
        temp_cost = cost # 전준 능력 적용 전 비용 저장
        cost = max(0, cost - 1)
        if cost < temp_cost: # 비용 감소가 실제로 일어났다면
            st.session_state.cost_reduction_active = False # 효과 1회용으로 소모
            # 로그는 execute_attack 등 실제 사용 시점에 찍는 것이 더 자연스러움

    # 유물에 의한 비용 감소 (인물 능력 적용 후)
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_cost_calculate" and card.name in art.effect["target_cards"]:
            cost = max(0, cost + art.effect["value"])

    # 최종적으로 기본 비용 증가분(+1) 적용
    final_cost = max(0, cost + 1) # 모든 계산 후 최종 비용 +1

    # 전준 효과 로그 추가 (실제 사용될 비용이 감소했는지 확인 후)
    if st.session_state.get('cost_reduction_active_just_used', False) and card.cost > final_cost:
        log_message(f"✨ [실무 지휘] 카드 비용 -1!", "info")
        st.session_state.cost_reduction_active_just_used = False # 로그 출력 플래그 리셋

    return final_cost


def execute_attack(card_index, tactic_index, penalty_mult=1.0):
    if card_index is None or card_index >= len(st.session_state.player_hand):
        st.toast("오류: 잘못된 카드 인덱스.", icon="🚨"); st.session_state.selected_card_index = None; st.rerun(); return
    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    company = st.session_state.current_battle_company
    is_residual = tactic_index >= len(company.tactics)
    tactic = ResidualTactic(company.tax_target - company.current_collected_tax) if is_residual else company.tactics[tactic_index]
    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); st.session_state.selected_card_index = None; st.rerun(); return

    # 전준 효과 사용 여부 확인 및 로그 처리 플래그 설정
    if st.session_state.get('cost_reduction_active', False) and cost < card.cost:
        st.session_state.cost_reduction_active = False # 효과 소모
        st.session_state.cost_reduction_active_just_used = True # 로그 출력용 플래그

    st.session_state.player_focus_current -= cost;
    if st.session_state.get('turn_first_card_played', True): st.session_state.turn_first_card_played = False

    base = card.base_damage; stage_bonus = 0; stage_bonus_log = ""
    basic_cards = ["단순 자료 대사", "기본 경비 적정성 검토", "단순 경비 처리 오류 지적", "세금계산서 대사"]
    current_stage = st.session_state.current_stage_level
    if card.name in basic_cards:
        if current_stage == 3: stage_bonus = 50
        elif current_stage == 2: stage_bonus = 30
        elif current_stage == 1: stage_bonus = 15
        if stage_bonus > 0: stage_bonus_log = f" (숙련 +{stage_bonus})"
    base_with_bonus = base + stage_bonus
    ref = 500; scale = (company.tax_target / ref)**0.5 if company.tax_target > 0 else 0.5; capped = max(0.5, min(2.0, scale)); scaled = int(base_with_bonus * capped); scale_log = f" (규모 보정: {base_with_bonus}→{scaled})" if capped != 1.0 or stage_bonus > 0 else ""; damage = scaled

    team_stats = st.session_state.team_stats; team_bonus = 0
    if any(c in [AttackCategory.COST, AttackCategory.COMMON] for c in card.attack_category): team_bonus += int(team_stats["analysis"] * 0.5)
    if AttackCategory.CAPITAL in card.attack_category: team_bonus += int(team_stats["data"] * 1.0)
    if '판례' in card.name: team_bonus += int(team_stats["persuasion"] * 1.0)
    if '압수' in card.name: team_bonus += int(team_stats["evidence"] * 1.5)
    if team_bonus > 0: log_message(f"📈 [팀 스탯 +{team_bonus}]", "info"); damage += team_bonus
    if "이찰수" in [m.name for m in st.session_state.player_team] and card.name in ["기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]: damage += 8; log_message("✨ [기본기] +8!", "info")
    if "임향수" in [m.name for m in st.session_state.player_team] and ('분석' in card.name or '자료' in card.name or '추적' in card.name or AttackCategory.CAPITAL in card.attack_category): bonus = int(team_stats["analysis"] * 0.1 + team_stats["data"] * 0.1); damage += bonus; log_message(f"✨ [기획 조사] +{bonus}!", "info")
    if "유재전" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.ERROR:
        bonus = int(team_stats["persuasion"] / 10)
        if bonus > 0: damage += bonus; log_message(f"✨ [정기 조사] +{bonus}!", "info")
    if "김태후" in [m.name for m in st.session_state.player_team] and AttackCategory.CAPITAL in card.attack_category:
        bonus = int(team_stats["evidence"] * 0.1)
        if bonus > 0: damage += bonus; log_message(f"✨ [심층 기획] +{bonus}!", "info")

    mult = 1.0; mult_log = ""
    if not is_residual and card.special_bonus and card.special_bonus.get('target_method') == tactic.method_type:
        m = card.special_bonus.get('multiplier', 1.0); mult *= m; mult_log += f"🔥[{card.special_bonus.get('bonus_desc')}] "
        if "조용규" in [m.name for m in st.session_state.player_team] and card.name == "판례 제시": mult *= 2; mult_log += "✨[세법 교본 x2] "
    if "한중후" in [m.name for m in st.session_state.player_team] and (company.size == "외국계" or company.size == "글로벌 기업" or tactic.method_type == MethodType.CAPITAL_TX): mult *= 1.3; mult_log += "✨[역외탈세 +30%] "
    if "서영택" in [m.name for m in st.session_state.player_team] and (company.size in ["대기업", "외국계", "글로벌 기업"]) and TaxType.CORP in card.tax_type: mult *= 1.25; mult_log += "✨[대기업 +25%] "
    if "이현동" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.INTENTIONAL: mult *= 1.2; mult_log += "✨[지하경제 +20%] "

    if penalty_mult != 1.0:
        mult_log += f"🤖[자동공격 페널티 x{penalty_mult:.2f}] "

    final_dmg = int(damage * mult * penalty_mult); overkill = 0; overkill_contrib = 0;

    if is_residual: dmg_tactic = final_dmg
    else:
        remain = tactic.total_amount - tactic.exposed_amount; dmg_tactic = min(final_dmg, remain);
        overkill = final_dmg - dmg_tactic; overkill_contrib = int(overkill * 0.5);
        tactic.exposed_amount += dmg_tactic;
    company.current_collected_tax += (dmg_tactic + overkill_contrib)

    attack_emoji = "💥"; prefix = "▶️ [적중]"
    is_crit = mult >= 2.0

    dmg_ratio = final_dmg / company.tax_target if company.tax_target > 0 else 0
    hit_level = 0
    if is_crit or dmg_ratio > 0.3:
        hit_level = 3
        prefix = "💥💥 [초 치명타!]"; st.balloons()
    elif mult > 1.0 or dmg_ratio > 0.15:
        hit_level = 2
        prefix = "🔥🔥 [치명타!]"
    elif final_dmg > 0:
        hit_level = 1
        prefix = "👍 [효과적!]"
    st.session_state.hit_effect_company = hit_level

    if AttackCategory.COST in card.attack_category: attack_emoji = "💸"
    elif AttackCategory.REVENUE in card.attack_category: attack_emoji = "📈"
    elif AttackCategory.CAPITAL in card.attack_category: attack_emoji = "🏦"
    elif card.name == "현장 압수수색": attack_emoji = "🔎"
    elif card.name == "판례 제시": attack_emoji = "⚖️"
    elif AttackCategory.COMMON in card.attack_category: attack_emoji = "📄"

    st.toast(f"{attack_emoji} {final_dmg}억원!", icon=attack_emoji)

    log_message(f"{prefix} '{card.name}' → '{tactic.name}'에 **{final_dmg}억원** 피해!{stage_bonus_log}{scale_log}", "success")
    if mult_log: log_message(f"  ㄴ {mult_log}", "info")
    # 전준 효과 로그 출력
    if st.session_state.get('cost_reduction_active_just_used', False):
        log_message(f"✨ [실무 지휘] 카드 비용 -1 적용!", "info")
        st.session_state.cost_reduction_active_just_used = False # 로그 플래그 리셋

    if not is_residual:
        if "금융" in card.name: log_message(f"💬 금융 분석팀: 의심스러운 자금 흐름 포착!", "info")
        elif "차명" in card.name: log_message(f"💬 조사팀: 은닉 계좌 추적 성공! 자금 흐름 확보!", "warning")
        elif "압수" in card.name: log_message(f"💬 현장팀: 결정적 증거물 확보!", "warning")
        elif "출처" in card.name: log_message(f"💬 조사팀: 자금 출처 소명 요구, 압박 수위 높임!", "info")
        elif tactic.method_type == MethodType.INTENTIONAL and final_dmg > tactic.total_amount * 0.5: log_message(f"💬 조사팀: 고의적 탈루 정황 가중! 추가 조사 필요.", "warning")
        elif tactic.method_type == MethodType.ERROR and '판례' in card.name: log_message(f"💬 법무팀: 유사 판례 제시하여 납세자 설득 중...", "info")
        if final_dmg < 10 and damage > 0: log_message(f"💬 조사관: 꼼꼼하게 증빙 대조 중...", "info")
        elif final_dmg > 100: log_message(f"💬 조사팀장: 결정적인 한 방입니다!", "success")
    if overkill > 0: log_message(f"📈 [초과 기여] 혐의 초과 {overkill}억 중 {overkill_contrib}억 추가 세액 확보!", "info")

    if not is_residual and tactic.exposed_amount >= tactic.total_amount and not getattr(tactic, '_logged_clear', False):
        setattr(tactic, 'is_cleared', True); setattr(tactic, '_logged_clear', True)
        log_message(f"🔥 [{tactic.name}] 혐의 완전 적발 완료! (총 {tactic.total_amount}억원)", "warning")
        if "벤츠" in card.text: log_message("💬 [현장] 법인소유 벤츠 키 확보!", "info")
        if "압수수색" in card.name: log_message("💬 [현장] 비밀장부 및 관련 증거물 다수 확보!", "info")

    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None;
    check_battle_end(); st.rerun()

# --- [수정] 자동 공격 체력 소모 5로 변경 ---
def execute_auto_attack():
    hp_cost = 5 # 체력 소모량
    if st.session_state.team_hp <= hp_cost: # 수정: hp_cost 비교
        st.toast(f"⚡ 자동 공격을 사용하기엔 팀 체력이 너무 낮습니다! (최소 {hp_cost+1} 필요)", icon="💔"); return

    affordable_attacks = []
    for i, card in enumerate(st.session_state.player_hand):
        if card.base_damage <= 0 or (card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]): continue
        cost = calculate_card_cost(card)
        if st.session_state.player_focus_current >= cost:
            affordable_attacks.append({'card': card, 'index': i, 'cost': cost})
    affordable_attacks.sort(key=lambda x: x['card'].base_damage, reverse=True)
    if not affordable_attacks:
        st.toast("⚡ 사용할 수 있는 자동 공격 카드가 없습니다.", icon="⚠️"); return

    company = st.session_state.current_battle_company; attack_executed = False
    all_tactics_cleared = all(t.is_cleared for t in company.tactics); target_not_met = company.current_collected_tax < company.tax_target

    for attack_info in affordable_attacks:
        current_card = attack_info['card']; current_idx = attack_info['index']; target_idx = -1
        if not all_tactics_cleared:
            for i, t in enumerate(company.tactics):
                if t.is_cleared: continue
                is_tax = (TaxType.COMMON in current_card.tax_type) or (isinstance(t.tax_type, list) and any(tt in current_card.tax_type for tt in t.tax_type)) or (t.tax_type in current_card.tax_type)
                is_cat = (AttackCategory.COMMON in current_card.attack_category) or (t.tactic_category in current_card.attack_category)
                if is_tax and is_cat: target_idx = i; break
        elif all_tactics_cleared and target_not_met:
             target_idx = len(company.tactics)

        if target_idx != -1:
            st.session_state.team_hp -= hp_cost # 수정: hp_cost 사용
            log_message(f"⚡ 자동 공격 사용! (팀 체력 -{hp_cost}, 피해량 25% 감소)", "warning")
            st.toast(f"⚡ 자동 공격! (❤️-{hp_cost}, 💥-25%)", icon="🤖") # 수정: hp_cost 표시
            target_name = "[잔여 혐의 조사]" if target_idx >= len(company.tactics) else company.tactics[target_idx].name
            log_message(f"⚡ 자동 공격: '{current_card.name}' -> '{target_name}'!", "info")

            execute_attack(current_idx, target_idx, penalty_mult=0.75) # 0.75 페널티 배율 전달

            attack_executed = True; break

    if not attack_executed:
        st.toast(f"⚡ 현재 손패의 카드로 공격 가능한 혐의가 없습니다.", icon="⚠️")

def develop_tax_logic(): # 과세 논리 개발
    hp_cost = math.ceil(st.session_state.team_hp / 2)
    if st.session_state.team_hp <= 1 or (st.session_state.team_hp - hp_cost) <= 0:
        st.toast("💡 체력이 너무 낮아 과세 논리를 개발할 수 없습니다.", icon="💔"); return

    st.session_state.team_hp -= hp_cost

    company = st.session_state.current_battle_company
    remaining_tactics = [t for t in company.tactics if not t.is_cleared]
    all_cleared = not remaining_tactics
    target_not_met = company.current_collected_tax < company.tax_target

    target_cats = set()
    target_methods = set()

    if remaining_tactics:
        for t in remaining_tactics:
            target_cats.add(t.tactic_category)
            if isinstance(t.tax_type, list): target_cats.update(t.tax_type)
            else: target_cats.add(t.tax_type)
            target_methods.add(t.method_type)
    elif all_cleared and target_not_met: # 잔여 혐의
        target_cats.add(AttackCategory.COMMON)
        target_methods.add(MethodType.ERROR)
    else:
        st.toast("💡 더 이상 분석할 혐의가 없습니다.", icon="ℹ️")
        st.session_state.team_hp += hp_cost # 체력 환불
        return

    best_card = None; max_score = -1

    for card in LOGIC_CARD_DB.values():
        if card.base_damage <= 0 or (card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]):
            continue # 공격 카드만 대상

        is_cat_match = (AttackCategory.COMMON in card.attack_category) or any(cat in target_cats for cat in card.attack_category)
        if not is_cat_match: continue

        score = card.base_damage

        if card.special_bonus and card.special_bonus.get('target_method') in target_methods:
            score *= card.special_bonus.get('multiplier', 1.0) * 1.5

        card_actual_cost = calculate_card_cost(card) # 현재 상태 기준 실제 비용 계산
        if card_actual_cost > 3: score *= 0.8
        if card_actual_cost <= 1 and card.base_damage > 0: score *= 1.1

        if score > max_score:
            max_score = score
            best_card = card

    if best_card:
        new_card = copy.deepcopy(best_card); new_card.just_created = True
        st.session_state.player_hand.append(new_card)
        log_message(f"💡 [과세 논리 개발] '{best_card.name}' 획득! (팀 체력 -{hp_cost})", "warning")
        st.toast(f"💡 '{best_card.name}' 획득! (❤️-{hp_cost})", icon="💡")
        st.session_state.hit_effect_player = True # 피격 효과
    else:
        log_message("💡 [과세 논리 개발] 적절한 카드를 찾지 못함.", "info")
        st.toast("💡 적절한 카드를 찾지 못했습니다.", icon="ℹ️")
        st.session_state.team_hp += hp_cost # 체력 환불

    st.rerun()


def end_player_turn():
    if 'kim_dj_effect_used' in st.session_state: st.session_state.kim_dj_effect_used = False
    if 'cost_reduction_active' in st.session_state: st.session_state.cost_reduction_active = False
    if 'cost_reduction_active_just_used' in st.session_state: st.session_state.cost_reduction_active_just_used = False
    st.session_state.player_discard.extend(st.session_state.player_hand); st.session_state.player_hand = []; st.session_state.selected_card_index = None
    log_message("--- 기업 턴 시작 ---"); enemy_turn()
    if not check_battle_end():
        start_player_turn()
        st.rerun()

def enemy_turn():
    co = st.session_state.current_battle_company; act = random.choice(co.defense_actions);
    # [수정] team_hp_damage는 생성자에서 이미 20% 증가됨
    min_d, max_d = co.team_hp_damage;
    dmg = random.randint(min_d, max_d); st.session_state.team_hp -= dmg
    st.session_state.hit_effect_player = True # 피격 효과 플래그
    st.toast(f"❤️ 팀 체력 -{dmg}!", icon="💔") # 피격 타격감
    log_icon = "🏢"
    if "로펌" in act or "법무팀" in act or "법리" in act: log_icon = "⚖️"
    elif "자료" in act or "서버" in act or "장부" in act: log_icon = "📁"
    elif "압력" in act or "여론전" in act or "항변" in act: log_icon = "🗣️"
    elif "도피" in act or "잠적" in act or "시간" in act: log_icon = "⏳"
    prefix = f"{log_icon} [기업]" if not (co.size in ["대기업", "외국계", "글로벌 기업"] and "로펌" in act) else f"{log_icon} [로펌]"; log_message(f"{prefix} {act} (팀 사기 저하 ❤️-{dmg}!)", "error")

# --- [수정] 전투 승리 시 35% 확률로 도구/팀원 추가 획득 로직 ---
def check_battle_end():
    company = st.session_state.current_battle_company
    if company.current_collected_tax >= company.tax_target:
        bonus = company.current_collected_tax - company.tax_target
        log_message(f"🎉 [조사 승리] 목표 {company.tax_target:,}억원 달성! (초과 {bonus:,}억원)", "success")
        st.session_state.total_collected_tax += company.current_collected_tax

        heal_amount = int(st.session_state.team_max_hp * 0.3)
        st.session_state.team_hp = min(st.session_state.team_max_hp, st.session_state.team_hp + heal_amount)
        log_message(f"🩺 [전투 승리] 팀 정비. (체력 +{heal_amount})", "success")
        st.toast(f"팀 체력 +{heal_amount} 회복!", icon="❤️")

        # --- [신규] 35% 확률로 조사 도구 추가 획득 ---
        if random.random() < 0.35:
            current_artifact_names = [art.name for art in st.session_state.player_artifacts]
            available_artifacts = [art for art in ARTIFACT_DB.values() if art.name not in current_artifact_names]
            if available_artifacts:
                new_artifact = random.choice(available_artifacts)
                st.session_state.player_artifacts.append(new_artifact)
                log_message(f"🎁 [전리품] 새로운 조사 도구 '{new_artifact.name}' 획득!", "success")
                st.toast(f"🎁 도구 획득: {new_artifact.name}!", icon="🧰")
                # 새 유물 획득 시 스탯 즉시 재계산 (예: 분기 보고서)
                recalculate_team_stats()

        # --- [신규] 35% 확률로 팀원 추가 획득 ---
        if random.random() < 0.35:
            current_member_names = [m.name for m in st.session_state.player_team]
            available_members = [m for m in TAX_MAN_DB.values() if m.name not in current_member_names]
            if available_members:
                new_member = random.choice(available_members)
                st.session_state.player_team.append(new_member)
                log_message(f"👥 [지원군] '{new_member.name}' 조사관 합류!", "success")
                st.toast(f"👥 팀원 합류: {new_member.name}!", icon="👨‍💼")
                # 새 팀원 합류 시 스탯 즉시 재계산
                recalculate_team_stats()

        st.session_state.game_state = "REWARD"
        last_card_text = ""
        if st.session_state.player_discard:
            try: last_card_text = st.session_state.player_discard[-1].text
            except IndexError: pass
        st.toast(f"승리! \"{last_card_text}\"" if last_card_text else "승리!", icon="🎉")
        return True
    if st.session_state.team_hp <= 0:
        st.session_state.team_hp = 0
        log_message("‼️ [조사 중단] 팀 체력 소진...", "error")
        st.session_state.game_state = "GAME_OVER"
        return True
    return False

def start_battle(co_template):
    co = copy.deepcopy(co_template); st.session_state.current_battle_company = co; st.session_state.game_state = "BATTLE"; st.session_state.battle_log = [f"--- {co.name} ({co.size}) 조사 시작 ---"]
    log_message(f"🏢 **{co.name}** 주요 탈루 혐의:", "info"); t_types = set();
    for t in co.tactics:
        tax = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value]
        log_message(f"- **{t.name}** ({'/'.join(tax)}, {t.method_type.value}, {t.tactic_category.value})", "info"); t_types.add(t.method_type)
    log_message("---", "info"); guide = "[조사 가이드] "; has_g = False
    if MethodType.INTENTIONAL in t_types: guide += "고의 탈루: 증거 확보, 압박 중요. "; has_g = True
    if MethodType.CAPITAL_TX in t_types or co.size in ["대기업", "외국계", "글로벌 기업"]: guide += "자본/국제 거래: 자금 흐름, 법규 분석 필요. "; has_g = True
    if MethodType.ERROR in t_types and MethodType.INTENTIONAL not in t_types: guide += "단순 오류: 규정/판례 제시, 설득 효과적. "; has_g = True
    log_message(guide if has_g else "[조사 가이드] 기업 특성/혐의 고려, 전략적 접근.", "warning"); log_message("---", "info")

    # 전투 시작 시 유물 효과 적용 (스탯 재계산에 포함됨)
    recalculate_team_stats()

    # 첫 턴 드로우 보너스 계산 (start_player_turn에서 사용)
    st.session_state.bonus_draw = 0
    for art in st.session_state.player_artifacts:
        log_message(f"✨ [조사도구] '{art.name}' 효과 준비.", "info")
        if art.effect["type"] == "on_battle_start" and art.effect["subtype"] == "draw":
            st.session_state.bonus_draw += art.effect["value"] # 첫 턴 드로우 카운트 누적

    st.session_state.player_deck.extend(st.session_state.player_discard); st.session_state.player_deck = random.sample(st.session_state.player_deck, len(st.session_state.player_deck)); st.session_state.player_discard = []; st.session_state.player_hand = [];
    start_player_turn()

def log_message(message, level="normal"):
    color = {"success": "green", "warning": "orange", "error": "red", "info": "blue"}.get(level)
    msg = f":{color}[{message}]" if color else message
    if 'battle_log' not in st.session_state: st.session_state.battle_log = []
    st.session_state.battle_log.insert(0, msg)
    if len(st.session_state.battle_log) > 50:
        st.session_state.battle_log.pop()

def go_to_next_stage(add_card=None):
    if add_card: st.session_state.player_deck.append(add_card); st.toast(f"[{add_card.name}] 덱 추가!", icon="🃏")

    if 'reward_cards' in st.session_state: del st.session_state.reward_cards
    st.session_state.current_stage_level += 1;
    if st.session_state.current_stage_level >= len(st.session_state.company_order):
        st.session_state.game_state = "GAME_CLEAR"
    else:
        st.session_state.game_state = "MAP"
    st.rerun()

# --- 5. UI 화면 함수 ---

def show_main_menu():
    st.title("💼 세무조사: 덱빌딩 로그라이크"); st.markdown("---")

    st.markdown("<h1 style='text-align: center; font-size: 80px; margin-bottom: 0px;'>⚖️</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-top: 0px;'>국세청 조사국</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.header("국세청에 오신 것을 환영합니다.")
    st.markdown("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")

    st.session_state.seed = st.number_input("RNG 시드 (0 = 랜덤)", value=0, step=1, help="동일 시드로 반복 테스트 가능")
    if st.button("🚨 조사 시작", type="primary", use_container_width=True):
        seed = st.session_state.get('seed', 0); random.seed(seed if seed != 0 else None)
        members = list(TAX_MAN_DB.values()); st.session_state.draft_team_choices = random.sample(members, min(len(members), 3))
        artifacts = list(ARTIFACT_DB.keys()); chosen_keys = random.sample(artifacts, min(len(artifacts), 3)); st.session_state.draft_artifact_choices = [ARTIFACT_DB[k] for k in chosen_keys]
        st.session_state.game_state = "GAME_SETUP_DRAFT"; st.rerun()

    with st.expander("📖 게임 방법", expanded=True):
        st.markdown("""
        **1. 🎯 목표**: 총 4단계(중소→중견→대기업→글로벌)의 기업 조사를 완료하고 승리.
        **2. ⚔️ 전투**: ❤️ **팀 체력**(0 시 패배), 🧠 **집중력**(카드 사용 자원).
        **3. ✨ 보너스**: 혐의 유형(`고의`, `오류`, `자본`)에 맞는 카드 사용 시 추가 피해!
        **4. 📈 성장**: 스테이지가 오를수록 기본 카드가 강해집니다. 전투 승리 시 확률적으로 **팀원**이나 **조사 도구** 획득!
        """) # 게임 방법 업데이트

    st.markdown(
        """
        <style>
        .watermark { ... } /* 스타일은 이전과 동일 */
        </style>
        <div class="watermark"> ... </div> /* 내용은 이전과 동일 */
        """, unsafe_allow_html=True
    )

# --- [수정] format_func에서 등급 표시 제거 (지난 요청에서 이미 반영됨) ---
def show_setup_draft_screen():
    st.title("👨‍💼 조사팀 구성"); st.markdown("팀 **리더**와 시작 **조사도구** 선택:")
    if 'draft_team_choices' not in st.session_state or 'draft_artifact_choices' not in st.session_state:
        st.error("드래프트 정보 없음..."); st.button("메인 메뉴로", on_click=lambda: st.session_state.update(game_state="MAIN_MENU")); return
    teams = st.session_state.draft_team_choices; arts = st.session_state.draft_artifact_choices
    st.markdown("---"); st.subheader("1. 팀 리더 선택:");
    lead_idx = st.radio("리더", range(len(teams)),
                        format_func=lambda i: f"**{teams[i].name}** | {teams[i].description}\n    └ **{teams[i].ability_name}**: {teams[i].ability_desc}", # 등급 제거됨
                        label_visibility="collapsed")
    st.markdown("---"); st.subheader("2. 시작 조사도구 선택:"); art_idx = st.radio("도구", range(len(arts)), format_func=lambda i: f"**{arts[i].name}** | {arts[i].description}", label_visibility="collapsed")
    st.markdown("---");
    if st.button("이 구성으로 조사 시작", type="primary", use_container_width=True):
        initialize_game(teams[lead_idx], arts[art_idx])
        del st.session_state.draft_team_choices, st.session_state.draft_artifact_choices
        st.rerun()

def show_map_screen():
    if 'current_stage_level' not in st.session_state:
        st.warning("게임 상태 초기화됨..."); st.session_state.game_state = "MAIN_MENU"; st.rerun(); return

    stage = st.session_state.current_stage_level
    stage_total = len(st.session_state.company_order)
    if stage == 0: group_name = "C 그룹 (중소기업)"
    elif stage == 1: group_name = "B 그룹 (중견기업)"
    elif stage == 2: group_name = "A 그룹 (국내 대기업)"
    else: group_name = "S 그룹 (글로벌 기업)"
    st.header(f"📍 조사 지역 (Stage {stage + 1} / {stage_total}) - {group_name}"); st.write("조사할 기업 선택:")

    companies = st.session_state.company_order
    if stage < len(companies):
        co = companies[stage]
# show_map_screen 함수 내부 ...
            with st.expander("🔍 혐의 및 실제 사례 정보 보기"):
                st.markdown("---"); st.markdown("### 📚 실제 사례 기반 교육 정보")
                # 교육 정보가 정상적으로 표시되는지 확인 (st.markdown 사용)
                st.markdown(co.real_case_desc)
                st.markdown("---"); st.markdown("### 📝 주요 탈루 혐의 분석")

                if not co.tactics:
                    st.write("(분석할 특정 탈루 혐의 없음)")
                else:
                    for i, t in enumerate(co.tactics):
                        try:
                            # --- [수정] AttributeError 방지 ---
                            if isinstance(t.tax_type, list):
                                # 리스트 내 요소가 .value 속성을 가지는지 확인 후 값 추출
                                t_types = [tx.value for tx in t.tax_type if hasattr(tx, 'value')]
                            elif hasattr(t.tax_type, 'value'):
                                # 단일 객체가 .value 속성을 가지는지 확인 후 값 추출
                                t_types = [t.tax_type.value]
                            else:
                                t_types = ["타입 오류"] # 예외 처리

                            # method_type과 tactic_category도 안전하게 .value 접근
                            method_val = t.method_type.value if hasattr(t.method_type, 'value') else "메소드 오류"
                            category_val = t.tactic_category.value if hasattr(t.tactic_category, 'value') else "카테고리 오류"
                            # --- 수정 끝 ---

                            st.markdown(f"**📌 {t.name}** (`{'/'.join(t_types)}`, `{method_val}`, `{category_val}`)\n> _{t.description}_")

                        except Exception as e:
                            st.error(f"혐의 '{t.name}' 표시 중 오류 발생: {e}")
                            # 오류 발생 시 해당 혐의 정보 대신 오류 메시지 출력
# ... 이하 함수 코드 동일 ...
            if st.button(f"🚨 {co.name} 조사 시작", type="primary", use_container_width=True):
                start_battle(co)
                st.rerun()
    else:
        st.session_state.game_state = "GAME_CLEAR"
        st.rerun()

# --- [수정] 손패 UI 대폭 축소 (col_hand) ---
def show_battle_screen():
    if not st.session_state.current_battle_company: st.error("오류: 기업 정보 없음..."); st.session_state.game_state = "MAP"; st.rerun(); return
    co = st.session_state.current_battle_company; st.title(f"⚔️ {co.name} 조사 중..."); st.markdown("---")
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

        st.progress(min(1.0, co.current_collected_tax/co.tax_target if co.tax_target > 0 else 1.0), text=f"💰 목표 세액: {co.current_collected_tax:,}/{co.tax_target:,} (억원)"); st.markdown("---"); st.subheader("🧾 탈루 혐의 목록")
        is_sel = st.session_state.get("selected_card_index") is not None
        if is_sel:
            if st.session_state.selected_card_index < len(st.session_state.player_hand):
                st.info(f"**'{st.session_state.player_hand[st.session_state.selected_card_index].name}'** 카드로 공격할 혐의 선택:")
            else: st.session_state.selected_card_index = None; st.rerun()

        all_tactics_cleared = all(getattr(t, 'is_cleared', False) for t in co.tactics)
        target_not_met = co.current_collected_tax < co.tax_target

        tactic_cont = st.container(height=450)
        with tactic_cont:
            if all_tactics_cleared and target_not_met:
                remaining_tax = co.tax_target - co.current_collected_tax
                res_t = ResidualTactic(remaining_tax)
                with st.container(border=True):
                    st.markdown(f"**{res_t.name}** (`공통`, `단순 오류`, `공통`)"); st.markdown(f"*{res_t.description}*")
                    st.progress(min(1.0, co.current_collected_tax/co.tax_target if co.tax_target > 0 else 1.0), text=f"남은 추징 목표: {remaining_tax:,}억원")
                    if is_sel and st.session_state.selected_card_index < len(st.session_state.player_hand):
                         if st.button(f"🎯 **{res_t.name}** 공격", key=f"attack_residual", use_container_width=True, type="primary"):
                             execute_attack(st.session_state.selected_card_index, len(co.tactics))
            elif all_tactics_cleared and not target_not_met:
                 st.success("모든 혐의 적발 완료! 목표 세액 달성!")
            elif not co.tactics : st.write("(조사할 특정 혐의 없음)")
            else:
                for i, t in enumerate(co.tactics):
                    cleared = getattr(t, 'is_cleared', False)
                    with st.container(border=True):
                        t_types = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value]; st.markdown(f"**{t.name}** (`{'/'.join(t_types)}`/`{t.method_type.value}`/`{t.tactic_category.value}`)\n*{t.description}*")
                        prog_txt = f"✅ 완료: {t.total_amount:,}억" if cleared else f"적발: {t.exposed_amount:,}/{t.total_amount:,}억"; st.progress(1.0 if cleared else (min(1.0, t.exposed_amount/t.total_amount) if t.total_amount > 0 else 1.0), text=prog_txt)
                        if is_sel and not cleared:
                            if st.session_state.selected_card_index < len(st.session_state.player_hand):
                                card = st.session_state.player_hand[st.session_state.selected_card_index]
                                is_tax = (TaxType.COMMON in card.tax_type) or (isinstance(t.tax_type, list) and any(tt in card.tax_type for tt in t.tax_type)) or (t.tax_type in card.tax_type)
                                is_cat = (AttackCategory.COMMON in card.attack_category) or (t.tactic_category in card.attack_category)
                                label, type, help = f"🎯 **{t.name}** 공격", "primary", "클릭하여 공격!"
                                if card.special_bonus and card.special_bonus.get('target_method') == t.method_type: label = f"💥 [특효!] **{t.name}** 공격"; help = f"클릭! ({card.special_bonus.get('bonus_desc')})"
                                disabled = False
                                if not is_tax: label, type, help, disabled = f"⚠️ (세목 불일치!)", "secondary", f"세목 불일치! '{', '.join(c.value for c in card.tax_type)}' 카드는 '{', '.join(t_types)}' 혐의에 사용 불가.", True
                                elif not is_cat: label, type, help, disabled = f"⚠️ (유형 불일치!)", "secondary", f"유형 불일치! '{', '.join(c.value for c in card.attack_category)}' 카드는 '{t.tactic_category.value}' 혐의에 사용 불가.", True
                                if st.button(label, key=f"attack_{i}", use_container_width=True, type=type, disabled=disabled, help=help):
                                    execute_attack(st.session_state.selected_card_index, i)
    with col_log:
        if st.session_state.get('hit_effect_player', False):
            st.error("💔 팀 현황 (피격!)")
        else:
            st.subheader("❤️ 팀 현황")
        c1, c2 = st.columns(2); c1.metric("팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}"); c2.metric("현재 집중력", f"{st.session_state.player_focus_current}/{st.session_state.player_focus_max}")
        if st.session_state.get('cost_reduction_active', False): st.info("✨ [실무 지휘] 다음 카드 비용 -1");

        st.subheader("📋 조사 기록 (로그)"); log_cont = st.container(height=300, border=True);
        for log in st.session_state.battle_log:
            log_cont.markdown(log)
        st.markdown("---"); st.subheader("🕹️ 행동")

        if st.session_state.get("selected_card_index") is not None:
            st.button("❌ 공격 취소", on_click=cancel_card_selection, use_container_width=True, type="secondary")
        else:
            act_cols = st.columns(2)
            act_cols[0].button("➡️ 턴 종료", on_click=end_player_turn, use_container_width=True, type="primary")
            with act_cols[1]:
                c1, c2 = st.columns(2)
                with c1:
                     # [수정] 자동 공격 도움말에 체력 소모량 5 반영
                    st.button("⚡ 자동", on_click=execute_auto_attack, use_container_width=True, type="secondary", help="[❤️-5, 💥-25% 페널티] 가장 강력한 카드로 자동 공격합니다.")

        with st.expander("💡 특별 지시 (고급 행동)"):
            st.button("과세 논리 개발 (❤️ 현재 체력 50% 소모)", on_click=develop_tax_logic, use_container_width=True, type="primary", help="현재 체력의 절반을 소모하여, 남은 혐의에 가장 유효하고 강력한 공격 카드 1장을 즉시 손패로 가져옵니다.")

    with col_hand:
        st.subheader(f"🃏 손패 ({len(st.session_state.player_hand)})")

        # --- [수정] 손패 UI 대폭 축소 ---
        # 고정 높이 컨테이너 사용 (스크롤 가능하게)
        hand_container = st.container(height=650) # 필요에 따라 높이 조절

        with hand_container:
            if not st.session_state.player_hand: st.write("(손패 없음)")

            for i, card in enumerate(st.session_state.player_hand):
                if i >= len(st.session_state.player_hand): continue
                cost = calculate_card_cost(card); afford = st.session_state.player_focus_current >= cost; color = "blue" if afford else "red"; selected = (st.session_state.get("selected_card_index") == i)

                with st.container(border=True):
                    # 제목 줄: 비용, 이름, 선택됨 여부
                    selected_str = ":blue[** (선택됨)**]" if selected else ""
                    title_line = f":{color}[**{cost}🧠**] **{card.name}**{selected_str}"

                    # 정보 줄: 피해량, 특효 등 (간략하게)
                    info_parts = []
                    if card.base_damage > 0: info_parts.append(f"💥{card.base_damage}억")
                    if card.special_bonus: info_parts.append(f"🔥{card.special_bonus.get('bonus_desc')}")
                    # 유틸리티 카드 정보
                    if not info_parts:
                        if card.special_effect and card.special_effect.get("type") == "draw":
                            info_parts.append(f"✨드로우 +{card.special_effect.get('value')}")
                        elif card.special_effect and card.special_effect.get("type") == "search_draw":
                            info_parts.append("🔍카드 서치")

                    info_line = " | ".join(info_parts)

                    # 한 줄에 제목과 정보 표시 (정보는 작게)
                    if info_line:
                        st.markdown(f"{title_line} <small>({info_line})</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(title_line) # 정보 없으면 제목만

                    # 버튼 (툴팁으로 상세 정보 제공)
                    btn_label = "선택" if (card.base_damage > 0) else "사용"
                    if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]: btn_label = "사용"

                    disabled = not afford
                    # 툴팁: 카드 상세 설명 + 태그 정보
                    c_types=[t.value for t in card.tax_type]; c_cats=[c.value for c in card.attack_category]
                    tooltip = f"[{card.name}] {card.description}\n세목:{'`,`'.join(c_types)} | 유형:{'`,`'.join(c_cats)}"
                    if not afford: tooltip = f"집중력 부족! ({cost})"

                    if st.button(btn_label, key=f"play_{i}", use_container_width=True, disabled=disabled, help=tooltip):
                        select_card_to_play(i)
        # --- 손패 UI 축소 끝 ---

# --- [수정] 팀 정비 탭 제거 (자동 회복으로 대체됨) ---
def show_reward_screen():
    st.header("🎉 조사 승리!"); st.balloons(); co = st.session_state.current_battle_company; st.success(f"**{co.name}** 조사 완료. 총 {co.current_collected_tax:,}억원 추징."); st.markdown("---")

    if st.session_state.current_stage_level >= len(st.session_state.company_order) - 1:
        st.session_state.game_state = "GAME_CLEAR"; st.rerun(); return

    st.subheader("🎁 획득할 카드 1장 선택")
    if 'reward_cards' not in st.session_state or not st.session_state.reward_cards:
        pool = [c for c in LOGIC_CARD_DB.values() if not (c.cost == 0 and c.special_effect and c.special_effect.get("type") == "draw")]
        opts = []; has_cap = any(t.method_type == MethodType.CAPITAL_TX for t in co.tactics)
        if has_cap:
            cap_cards = [c for c in pool if AttackCategory.CAPITAL in c.attack_category and c not in opts]
            if cap_cards:
                opts.append(random.choice(cap_cards)); st.toast("ℹ️ [보상 가중치] '자본' 카드 1장 포함!")
        remain = [c for c in pool if c not in opts]; num_add = 3 - len(opts)
        if len(remain) < num_add: opts.extend(random.sample(remain, len(remain)))
        else: opts.extend(random.sample(remain, num_add))
        while len(opts) < 3 and len(pool) > 0:
             add = random.choice(pool)
             if add not in opts or len(pool) < 3: opts.append(add)
        st.session_state.reward_cards = opts

    cols = st.columns(len(st.session_state.reward_cards))
    for i, card in enumerate(st.session_state.reward_cards):
        with cols[i]:
            with st.container(border=True):
                types=[t.value for t in card.tax_type]; cats=[c.value for c in card.attack_category];
                # [수정] 카드 비용 표시는 실제 비용(calculate_card_cost) 대신 기본 비용(card.cost) 표시
                st.markdown(f"**{card.name}**|비용:{card.cost}🧠");
                st.caption(f"세목:`{'`,`'.join(types)}`|유형:`{'`,`'.join(cats)}`"); st.markdown(card.description);
                if card.base_damage > 0: st.info(f"**기본 적출액:** {card.base_damage} 억원")
                elif card.special_effect and card.special_effect.get("type") == "draw": st.info(f"**드로우:** +{card.special_effect.get('value', 0)}")
                if card.special_bonus: st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")

                if st.button(f"선택: {card.name}", key=f"reward_{i}", use_container_width=True, type="primary"):
                    go_to_next_stage(add_card=card)

    st.markdown("---")
    st.button("카드 획득 안 함 (다음 스테이지로)", on_click=go_to_next_stage, type="secondary", use_container_width=True)


def show_game_over_screen():
    st.header("... 조사 중단 ..."); st.error("팀 체력 소진.")
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax:,} 억원"); st.metric("진행 스테이지", f"📍 {st.session_state.current_stage_level + 1} / 4")
    st.image("https://images.unsplash.com/photo-1518340101438-1d16873c3a88?q=80&w=1740&auto=format&fit=crop", caption="조사에 지친 조사관들...", width=400)
    st.button("다시 도전", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), type="primary", use_container_width=True)

def show_game_clear_screen():
    st.header("🎉 조사 완료!"); st.balloons()
    st.success(f"축하합니다! 4단계의 조사를 모두 성공적으로 완료했습니다.")
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax:,} 억원")
    st.metric("진행 스테이지", f"📍 4 / 4")
    st.image("https://images.unsplash.com/photo-1517048676732-d65bc937f952?q=80&w=1740&auto=format&fit=crop", caption="성공적으로 임무를 완수한 조사팀.", width=400)
    st.button("🏆 메인 메뉴로 돌아가기", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), type="primary", use_container_width=True)

# --- [수정] 사이드바 팀원 수 동적 표시, 등급 제거 ---
def show_player_status_sidebar():
    with st.sidebar:
        st.title("👨‍💼 조사팀 현황"); st.metric("💰 총 추징 세액", f"{st.session_state.total_collected_tax:,} 억원")
        st.metric("❤️ 현재 팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}")

        st.markdown("---")
        with st.expander("📊 팀 스탯", expanded=False):
            stats = st.session_state.team_stats; st.markdown(f"- 분석력: {stats['analysis']}\n- 설득력: {stats['persuasion']}\n- 증거력: {stats['evidence']}\n- 데이터: {stats['data']}")

        # [수정] 팀원 수 동적 표시
        st.subheader(f"👥 팀원 ({len(st.session_state.player_team)}명)")
        for m in st.session_state.player_team:
             # 등급 제거됨
             with st.expander(f"**{m.name}**"):
                 st.markdown(f"HP:{m.hp}/{m.max_hp}, Focus:{m.focus}\n**{m.ability_name}**: {m.ability_desc}\n({m.description})")

        st.markdown("---")
        total = len(st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand); st.subheader(f"📚 보유 덱 ({total}장)")
        with st.expander("덱 구성 보기"):
            deck = st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand; counts = {};
            for card in deck: counts[card.name] = counts.get(card.name, 0) + 1
            for name in sorted(counts.keys()):
                st.write(f"- {name} x {counts[name]}")
        if st.session_state.game_state == "BATTLE":
            with st.expander("🗑️ 버린 덱 보기"):
                discard_counts = {name: 0 for name in counts};
                for card in st.session_state.player_discard: discard_counts[card.name] = discard_counts.get(card.name, 0) + 1
                if not any(v > 0 for v in discard_counts.values()): st.write("(버린 카드 없음)")
                else:
                    for n, c in sorted(discard_counts.items()):
                        if c > 0: st.write(f"- {n} x {c}")
        st.markdown("---"); st.subheader("🧰 보유 도구")
        if not st.session_state.player_artifacts: st.write("(없음)")
        else:
            for art in st.session_state.player_artifacts:
                st.success(f"- {art.name}: {art.description}")
        st.markdown("---"); st.button("게임 포기 (메인 메뉴)", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), use_container_width=True)

# --- 6. 메인 실행 로직 ---
def main():
    st.set_page_config(page_title="세무조사 덱빌딩", layout="wide", initial_sidebar_state="expanded")
    if 'game_state' not in st.session_state: st.session_state.game_state = "MAIN_MENU"

    running = ["MAP", "BATTLE", "REWARD"]

    if st.session_state.game_state in running and 'player_team' not in st.session_state:
        st.toast("⚠️ 세션 만료, 메인 메뉴로."); st.session_state.game_state = "MAIN_MENU"; st.rerun(); return

    pages = {
        "MAIN_MENU": show_main_menu,
        "GAME_SETUP_DRAFT": show_setup_draft_screen,
        "MAP": show_map_screen,
        "BATTLE": show_battle_screen,
        "REWARD": show_reward_screen,
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

