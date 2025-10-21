import streamlit as st
import random
import copy
from enum import Enum
import math

# --- 0. Enum(열거형) 정의 ---
class TaxType(str, Enum): CORP = "법인세"; VAT = "부가세"; COMMON = "공통"
class AttackCategory(str, Enum): COST = "비용"; REVENUE = "수익"; CAPITAL = "자본"; COMMON = "공통"
class MethodType(str, Enum): INTENTIONAL = "고의적 누락"; ERROR = "단순 오류"; CAPITAL_TX = "자본 거래"

# --- 헬퍼 함수 ---
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
    def __init__(self, name, grade_num, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost); self.grade_num=grade_num; self.hp=hp; self.max_hp=hp; self.focus=focus; self.analysis=analysis; self.persuasion=persuasion; self.evidence=evidence; self.data=data; self.ability_name=ability_name; self.ability_desc=ability_desc; grade_map={4:"S", 5:"S", 6:"A", 7:"B", 8:"C", 9:"C"}; self.grade=grade_map.get(self.grade_num, "C")
class LogicCard(Card):
    def __init__(self, name, description, cost, base_damage, tax_type: list[TaxType], attack_category: list[AttackCategory], text, special_effect=None, special_bonus=None):
        super().__init__(name, description, cost); self.base_damage=base_damage; self.tax_type=tax_type; self.attack_category=attack_category; self.text=text; self.special_effect=special_effect; self.special_bonus=special_bonus;
class EvasionTactic:
    def __init__(self, name, description, total_amount, tax_type: TaxType | list[TaxType], method_type: MethodType, tactic_category: AttackCategory):
        self.name=name; self.description=description; self.total_amount=total_amount; self.exposed_amount=0; self.tax_type=tax_type; self.method_type=method_type; self.tactic_category=tactic_category; self.is_cleared=False;
# [신규] 잔여 혐의 조사를 위한 더미 Tactic 클래스 (is_cleared 무시)
class ResidualTactic(EvasionTactic):
     def __init__(self):
         super().__init__(name="[잔여 혐의 조사]", description="모든 특정 혐의가 적발되었습니다. 목표 세액 달성을 위해 남은 부분을 조사합니다.", total_amount=99999, tax_type=[TaxType.COMMON], method_type=MethodType.ERROR, tactic_category=AttackCategory.COMMON)
     @property
     def is_cleared(self): return False # 항상 공격 가능하도록
     @is_cleared.setter
     def is_cleared(self, value): pass # is_cleared 상태 변경 무시

class Company:
    def __init__(self, name, size, description, real_case_desc, revenue, operating_income, tax_target, team_hp_damage, tactics, defense_actions):
        self.name=name; self.size=size; self.description=description; self.real_case_desc=real_case_desc; self.revenue=revenue; self.operating_income=operating_income; self.tax_target=tax_target; self.team_hp_damage=team_hp_damage; self.current_collected_tax=0; self.tactics=tactics; self.defense_actions=defense_actions;
class Artifact:
    def __init__(self, name, description, effect): self.name=name; self.description=description; self.effect=effect;

# --- 2. 게임 데이터베이스 (DB) ---
TAX_MAN_DB = { # 조사관 설명 길이 약간 조정
    "lim": TaxManCard(name="임향수", grade_num=4, description="조사통의 대부. 대기업 비자금, 불법 증여 조사 지휘 경험 풍부.", cost=0, hp=120, focus=3, analysis=10, persuasion=10, evidence=10, data=10, ability_name="[기획 조사]", ability_desc="매 턴 집중력+1. 분석/데이터 스탯 비례 비용/자본 카드 피해량 증가."),
    "han": TaxManCard(name="한중히", grade_num=5, description="국제조세 전문가. OECD 파견 경험으로 국제 공조 및 BEPS 이해 깊음.", cost=0, hp=80, focus=2, analysis=9, persuasion=6, evidence=8, data=9, ability_name="[역외탈세 추적]", ability_desc="'외국계' 기업 또는 '자본 거래' 혐의 공격 시 최종 피해량 +30%."),
    "baek": TaxManCard(name="백용호", grade_num=5, description="세제 전문가. TIS, NTIS 등 과학세정 인프라 구축 경험.", cost=0, hp=90, focus=2, analysis=7, persuasion=10, evidence=9, data=7, ability_name="[TIS 분석]", ability_desc="'금융거래 분석', '빅데이터 분석' 등 데이터 관련 카드 비용 -1."),
    "seo": TaxManCard(name="서영택", grade_num=6, description="조사 전문가. 변칙 상속/증여 조사를 강력 지휘. 대기업 조사 정통.", cost=0, hp=100, focus=2, analysis=8, persuasion=9, evidence=8, data=7, ability_name="[대기업 저격]", ability_desc="'대기업', '외국계' 기업의 '법인세' 혐의 카드 공격 시 최종 피해량 +25%."),
    "kim_dj": TaxManCard(name="김대지", grade_num=5, description="세정 운영 전문가. 데이터 기반 대규모 조사 경험.", cost=0, hp=90, focus=2, analysis=10, persuasion=7, evidence=7, data=10, ability_name="[부동산 투기 조사]", ability_desc="팀 '데이터' 스탯 50+ 시, 턴 시작 시 '금융거래 분석' 카드 1장 생성."),
    "lee_hd": TaxManCard(name="이현동", grade_num=5, description="강력한 추진력의 조사통. 지하경제 양성화 및 역외탈세 추적 의지 강함.", cost=0, hp=100, focus=3, analysis=7, persuasion=8, evidence=10, data=8, ability_name="[지하경제 양성화]", ability_desc="'고의적 누락(Intentional)' 혐의 공격의 최종 피해량 +20%."),
    "kim": TaxManCard(name="김철주", grade_num=6, description="현장 전문가. 서울청 조사4국 '지하경제 양성화' 관련 조사 다수 수행.", cost=0, hp=110, focus=2, analysis=6, persuasion=8, evidence=9, data=5, ability_name="[압수수색]", ability_desc="'현장 압수수색' 카드 사용 시 15% 확률로 '결정적 증거' 추가 획득."),
    "oh": TaxManCard(name="전필성", grade_num=7, description="[가상] 데이터 전문가. TIS 초기 멤버로 시스템 이해도 높음. 신종 거래 분석 능함.", cost=0, hp=110, focus=2, analysis=7, persuasion=6, evidence=7, data=8, ability_name="[데이터 마이닝]", ability_desc="기본 적출액 70억 이상 '데이터' 관련 카드(자금출처조사 등) 피해량 +15."),
    "jo": TaxManCard(name="조용규", grade_num=7, description="세법 이론가. 교육원 교수 경험. 법리 해석과 판례 분석 뛰어남.", cost=0, hp=80, focus=3, analysis=9, persuasion=7, evidence=6, data=7, ability_name="[세법 교본]", ability_desc="'판례 제시', '법령 재검토' 카드의 효과(피해량/드로우) 2배 적용."),
    "park": TaxManCard(name="박지연", grade_num=8, description="[가상] 세법 신동. 세무사/CPA 동시 합격 특채. 날카로운 법리 검토 능력.", cost=0, hp=70, focus=3, analysis=7, persuasion=5, evidence=6, data=7, ability_name="[법리 검토]", ability_desc="턴마다 처음 사용하는 '분석' 또는 '설득' 유형 카드의 비용 -1."),
    "lee": TaxManCard(name="이철수", grade_num=7, description="[가상] 7급 공채 신입. 열정 넘치나 경험 부족. 기본기 충실.", cost=0, hp=80, focus=2, analysis=5, persuasion=5, evidence=5, data=5, ability_name="[기본기]", ability_desc="'기본 경비 적정성 검토', '단순 경비 처리 오류 지적' 카드 피해량 +8."),
    "ahn_wg": TaxManCard(name="안원구", grade_num=6, description="특수 조사의 귀재. 서울청 조사국 등에서 대기업 비자금 등 특수 조사 경험 풍부.", cost=0, hp=110, focus=2, analysis=8, persuasion=5, evidence=10, data=6, ability_name="[특수 조사]", ability_desc="'현장 압수수색', '차명계좌 추적' 카드 비용 -1 (최소 0)."),
    "yoo_jj": TaxManCard(name="유재준", grade_num=6, description="[현직] 관리자. 서울청 조사2국 대기업 정기 조사 및 상속/증여세 조사 담당. 분석/설득 강점.", cost=0, hp=100, focus=2, analysis=8, persuasion=7, evidence=7, data=7, ability_name="[정기 조사 전문]", ability_desc="'단순 오류(Error)' 혐의 공격 시, 팀 '설득' 스탯 10당 피해량 +1."),
    "kim_th": TaxManCard(name="김태호", grade_num=6, description="[현직] 관리자. 중부청 조사1국 대기업/중견기업 심층 기획 및 국제거래 조사 담당. 증거 확보/데이터 분석 탁월.", cost=0, hp=105, focus=2, analysis=9, persuasion=5, evidence=9, data=8, ability_name="[심층 기획 조사]", ability_desc="'자본 거래(Capital Tx)' 혐의 공격 시, 팀 '증거' 스탯의 10%만큼 추가 피해."),
    "jeon_j": TaxManCard(name="전진", grade_num=7, description="[현직] 실무 과장. 중부청 조사1국. 조사 현장 지휘 경험 풍부, 팀원 능력 활용 능숙.", cost=0, hp=85, focus=3, analysis=7, persuasion=6, evidence=6, data=6, ability_name="[실무 지휘]", ability_desc="턴 시작 시, **팀**의 다음 카드 사용 비용 -1.")
}
LOGIC_CARD_DB = { # 보호막 카드 제외
    "c_tier_01": LogicCard(name="단순 자료 대사", cost=0, base_damage=5, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="매입/매출 자료 단순 비교.", text="자료 대사 기본 습득."),
    "c_tier_02": LogicCard(name="법령 재검토", cost=0, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 1장 뽑기.", text="관련 법령 재검토.", special_effect={"type": "draw", "value": 1}),
    "util_01": LogicCard(name="초과근무", cost=1, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="카드 2장 뽑기.", text="밤샘 근무로 단서 발견!", special_effect={"type": "draw", "value": 2}),
    "basic_01": LogicCard(name="기본 경비 적정성 검토", cost=1, base_damage=10, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="기본 비용 처리 적정성 검토.", text="법인세법 비용 조항 분석."),
    "basic_02": LogicCard(name="단순 경비 처리 오류 지적", cost=1, base_damage=12, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="증빙 미비 경비 지적.", text="증빙 대조 기본 습득."),
    "b_tier_04": LogicCard(name="세금계산서 대사", cost=1, base_damage=15, tax_type=[TaxType.VAT], attack_category=[AttackCategory.REVENUE, AttackCategory.COST], description="매입/매출 세금계산서 합계표 대조.", text="합계표 불일치 확인."),
    "c_tier_03": LogicCard(name="가공 증빙 수취 분석", cost=2, base_damage=15, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.COST], description="실물 거래 없이 세금계산서만 수취한 정황을 분석합니다.", text="가짜 세금계산서 흐름 파악."),
    "corp_01": LogicCard(name="접대비 한도 초과", cost=2, base_damage=25, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="법정 한도를 초과한 접대비를 비용으로 처리한 부분을 지적합니다.", text="법인세법 접대비 조항 습득."),
    "b_tier_03": LogicCard(name="판례 제시", cost=2, base_damage=22, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="유사한 탈루 또는 오류 사례에 대한 과거 판례를 제시하여 설득합니다.", text="대법원 판례 제시.", special_bonus={'target_method': MethodType.ERROR, 'multiplier': 2.0, 'bonus_desc': '단순 오류에 2배 피해'}),
    "b_tier_05": LogicCard(name="인건비 허위 계상", cost=2, base_damage=30, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="실제 근무하지 않는 친인척 등에게 급여를 지급한 것처럼 꾸며 비용 처리한 것을 적발합니다.", text="급여대장-근무 내역 불일치 확인."),
    "util_02": LogicCard(name="빅데이터 분석", cost=2, base_damage=0, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="적 혐의 유형과 일치하는 카드 1장 서치.", text="TIS 빅데이터 패턴 발견!", special_effect={"type": "search_draw", "value": 1}),
    "corp_02": LogicCard(name="업무 무관 자산 비용 처리", cost=3, base_damage=35, tax_type=[TaxType.CORP], attack_category=[AttackCategory.COST], description="대표이사 개인 차량 유지비, 가족 해외여행 경비 등 업무와 관련 없는 비용을 법인 비용으로 처리한 것을 적발합니다.", text="벤츠 운행일지 확보!", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 1.5, 'bonus_desc': '고의적 누락에 1.5배 피해'}),
    "cap_01": LogicCard(name="부당행위계산부인", cost=3, base_damage=40, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL, AttackCategory.REVENUE], description="특수관계자와의 거래(자산 고가 매입, 저가 양도 등)에서 시가를 조작하여 이익을 분여한 혐의를 지적합니다.", text="계열사 간 저가 양수도 적발.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
    "b_tier_01": LogicCard(name="금융거래 분석", cost=3, base_damage=45, tax_type=[TaxType.CORP], attack_category=[AttackCategory.REVENUE, AttackCategory.CAPITAL], description="의심스러운 자금 흐름을 추적하여 숨겨진 수입이나 부당한 자본 거래를 포착합니다.", text="FIU 분석 기법 습득."),
    "b_tier_02": LogicCard(name="현장 압수수색", cost=3, base_damage=25, tax_type=[TaxType.COMMON], attack_category=[AttackCategory.COMMON], description="조사 현장을 방문하여 장부와 실제 재고, 자산 등을 대조하고 숨겨진 자료를 확보합니다.", text="재고 불일치 확인.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "a_tier_02": LogicCard(name="차명계좌 추적", cost=3, base_damage=50, tax_type=[TaxType.CORP, TaxType.VAT], attack_category=[AttackCategory.REVENUE], description="타인 명의로 개설된 계좌를 통해 수입 금액을 은닉한 정황을 포착하고 자금 흐름을 추적합니다.", text="차명계좌 흐름 파악.", special_bonus={'target_method': MethodType.INTENTIONAL, 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}),
    "cap_02": LogicCard(name="불공정 자본거래", cost=4, base_damage=80, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="합병, 증자, 감자 등 과정에서 불공정한 비율을 적용하여 주주(총수 일가)에게 이익을 증여한 혐의를 조사합니다.", text="상증세법상 이익의 증여.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "a_tier_01": LogicCard(name="자금출처조사", cost=4, base_damage=90, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="고액 자산가의 자산 형성 과정에서 불분명한 자금의 출처를 소명하도록 요구하고, 탈루 혐의를 조사합니다.", text="수십 개 차명계좌 흐름 파악."),
    "s_tier_01": LogicCard(name="국제거래 과세논리", cost=4, base_damage=65, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="이전가격 조작, 고정사업장 회피 등 국제거래를 이용한 조세회피 전략을 분석하고 과세 논리를 개발합니다.", text="BEPS 보고서 이해.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}),
    "s_tier_02": LogicCard(name="조세피난처 역외탈세", cost=5, base_damage=130, tax_type=[TaxType.CORP], attack_category=[AttackCategory.CAPITAL], description="조세피난처에 설립된 특수목적회사(SPC) 등을 이용하여 해외 소득을 은닉한 역외탈세 혐의를 조사합니다.", text="BVI, 케이맨 SPC 실체 규명.", special_bonus={'target_method': MethodType.CAPITAL_TX, 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}),
}
ARTIFACT_DB = { # 보호막 아티팩트 제외
    "coffee": Artifact(name="☕ 믹스 커피", description="턴 시작 시 집중력 +1.", effect={"type": "on_turn_start", "value": 1, "subtype": "focus"}),
    "forensic": Artifact(name="💻 포렌식 장비", description="팀 '증거(Evidence)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_evidence"}),
    "plan": Artifact(name="📜 조사계획서", description="첫 턴 카드 +1장.", effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}),
    "recorder": Artifact(name="🎤 녹음기", description="팀 '설득(Persuasion)' 스탯 +5.", effect={"type": "on_battle_start", "value": 5, "subtype": "stat_persuasion"}),
    "book": Artifact(name="📖 오래된 법전", description="'판례 제시', '법령 재검토' 비용 -1.", effect={"type": "on_cost_calculate", "value": -1, "target_cards": ["판례 제시", "법령 재검토"]})
}
# --- [수정됨] 기업 정보 최신화 ---
COMPANY_DB = [
    Company(
        name="(주)가나푸드", size="소규모", revenue=8000, operating_income=800, tax_target=5, team_hp_damage=(5, 10),
        description="중소 유통업체. 대표 SNS는 **슈퍼카**와 **명품 시계** 사진으로 가득합니다.",
        real_case_desc="[교육] 소규모 법인은 대표가 법인 자금을 개인 돈처럼 사용하는 경우가 빈번합니다. **법인카드**로 명품을 구매하거나, **개인 차량 유지비**를 처리하는 행위 등은 '**업무 무관 비용**'으로 간주되어 비용으로 인정받지 못합니다 (**손금 불인정**). 또한, 해당 금액은 대표의 **상여**로 처리되어 **소득세**가 추가로 과세될 수 있습니다.",
        tactics=[
            EvasionTactic("사주 개인적 사용", "대표가 배우자 명의의 **외제차 리스료** (월 500만원), 주말 **골프 비용**, 자녀 **학원비** 등을 **법인카드**로 결제.", 3, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST),
            EvasionTactic("증빙 미비 경비", "실제 거래 없이 서류상으로만 **거래처 명절 선물** 1천만원을 지출한 것처럼 꾸미고, 관련 **증빙**(세금계산서, 입금표 등)을 제시하지 못함.", 2, [TaxType.CORP, TaxType.VAT], MethodType.ERROR, AttackCategory.COST)
        ], defense_actions=["담당 세무사가 시간 끌기.", "대표가 '사실무근' 주장.", "경리 직원이 '실수' 변명."]
    ),
    Company(
        name="㈜넥신 (Nexin)", size="중견기업", revenue=180000, operating_income=12000, tax_target=90, team_hp_damage=(15, 30), # 스탯 상향
        description="최근 급성장한 **게임/IT 기업**. **R&D 투자**가 많고 임직원 **스톡옵션** 부여가 잦습니다.",
        real_case_desc="[교육] IT 기업은 **연구개발(R&D) 세액공제** 적용 요건이 까다롭고 변경이 잦아 오류가 발생하기 쉽습니다. 특히 **인건비**나 **위탁개발비**의 적격 여부가 주된 쟁점입니다. 또한, 임직원에게 부여한 **스톡옵션**의 경우, 행사 시점의 **시가 평가** 및 과세 방식(근로소득 vs 기타소득)에 대한 검토가 필요하며, 이를 이용한 **세금 회피** 시도가 있을 수 있습니다.",
        tactics=[
            EvasionTactic("R&D 비용 부당 공제", "**연구개발 활동**과 직접 관련 없는 **인건비** 및 **일반 관리비** 50억원을 **R&D 세액공제** 대상 비용으로 허위 계상.", 50, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST),
            EvasionTactic("스톡옵션 시가 저가 평가", "임원에게 부여한 **스톡옵션** 행사 시 **비상장주식 가치**를 의도적으로 낮게 평가하여 **소득세(근로소득)** 40억원 탈루.", 40, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL) # 법인세법상 손금 이슈도 연관될 수 있음
        ], defense_actions=["회계법인이 '적격 R&D' 주장.", "자료가 '클라우드 서버 오류'로 삭제 주장.", "스톡옵션 평가는 '외부 기관 용역' 결과라며 책임 회피."]
    ),
    Company(
        name="(주)한늠석유 (자료상)", size="중견기업", revenue=60000, operating_income=-500, tax_target=120, team_hp_damage=(20, 35), # 스탯 상향
        description="전형적인 '**자료상**' 의심 업체. **유가보조금 부정수급** 및 **허위 세금계산서** 발행 전력.",
        real_case_desc="[교육] 최근 자료상은 **허위 세금계산서** 수수를 넘어 **유가보조금 부정수급**, **면세유 불법 유통** 등 다양한 방식으로 진화하고 있습니다. 여러 단계의 **페이퍼컴퍼니**를 동원하여 추적을 어렵게 만들며, **대포통장**과 **차명계좌**를 이용해 자금을 세탁합니다. 이는 **조세범처벌법** 및 **특정범죄가중처벌법** 위반으로 엄중히 처벌됩니다.",
        tactics=[
            EvasionTactic("유가보조금 부정수급", "**허위 세금계산서**를 이용해 **가짜 경유** 거래를 꾸며 **유가보조금** 80억원을 부정하게 수령.", 80, [TaxType.VAT, TaxType.COMMON], MethodType.INTENTIONAL, AttackCategory.REVENUE), # 보조금은 수익으로 볼 수 있음
            EvasionTactic("가공 세금계산서 발행", "**실물 거래 없이** 다른 주유소 등에 **허위 세금계산서** 40억원 상당을 발행해주고 수수료 수취.", 40, TaxType.VAT, MethodType.INTENTIONAL, AttackCategory.COST) # 매출원가 부풀리기 목적
        ], defense_actions=["대표 해외 도피 시도.", "사무실 잠적 (페이퍼컴퍼니).", "관련 장부 소각 및 증거 인멸 시도."]
    ),
     Company(
        name="㈜삼숭물산 (Samsoong)", size="대기업", revenue=60_000_000, operating_income=2_500_000, tax_target=1200, team_hp_damage=(20, 40), # 스탯 상향
        description="대한민국 대표 **대기업 그룹**의 주력 계열사. **경영권 승계** 및 **해외 투자** 관련 이슈.",
        real_case_desc="[교육] 대기업은 **경영권 승계** 과정에서의 **일감 몰아주기**, **불공정 합병** 외에도, **해외 현지법인**을 이용한 세금 탈루가 빈번합니다. **이전가격 조작**을 통해 국내 소득을 해외로 이전하거나, **조세피난처**에 설립한 법인을 통해 **배당 소득** 등을 은닉하는 방식입니다. **국제조세조정에 관한 법률** 및 **외국환거래법** 등 복잡한 법규 검토가 필요합니다.",
        tactics=[
            EvasionTactic("일감 몰아주기", "**총수 2세** 보유 **비상장 계열사**에 그룹 **SI 용역** 고가 발주, 연 수천억원 부당 지원.", 500, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL),
            EvasionTactic("불공정 합병", "**총수 일가**에 유리하도록 계열사 간 **합병 비율** 조작, **경영권 승계** 및 **이익 증여**.", 300, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL), # 금액 조정
            EvasionTactic("해외 현지법인 소득 누락", "**베트남 현지법인**의 이익잉여금 수천억원을 **배당**하지 않고 은닉하거나, 불필요한 **경영자문료** 명목으로 국내 자금 유출.", 400, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE) # 신규 혐의 추가
        ], defense_actions=["**김&장** 등 최고 로펌 동원.", "로펌 '정상 경영 활동' 의견서 제출.", "언론에 '**과도한 세무조사**' 여론전.", "정치권 통해 조사 무마 시도."]
    ),
    Company(
        name="구갈 코리아(유) (Googal)", size="외국계", revenue=2_500_000, operating_income=350_000, tax_target=900, team_hp_damage=(18, 35), # 스탯 상향
        description="글로벌 **IT 공룡**의 한국 지사. **이전가격**, **고정사업장** 관련 공격적 조세회피 의심.",
        real_case_desc="[교육] 다국적 IT 기업들은 **조세 조약** 및 **세법** 허점을 이용한 '**공격적 조세회피**(ATP)' 전략을 구사합니다. **저세율국** 자회사에 '**IP 사용료**', '**경영자문료**' 명목으로 이익을 이전시키는 '**이전가격**(TP)' 조작, 국내 **고정사업장** 존재 사실 은폐 등이 대표적입니다. **OECD BEPS 프로젝트**에 따른 국제 공조 강화로 대응 중입니다.",
        tactics=[
            EvasionTactic("이전가격(TP) 조작 - IP 사용료", "**아일랜드** 법인에 국내 매출의 과도한 부분을 '**IP 사용료**'로 지급하여 국내 소득 축소.", 500, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL),
            EvasionTactic("고정사업장 회피", "국내 **서버 운영** 및 **광고 계약 체결** 등 실질적 영업 활동에도 불구, '**단순 지원 용역**'으로 위장하여 **고정사업장** 신고 회피.", 400, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE) # 금액 상향
        ], defense_actions=["미국 본사 '**영업 비밀**' 이유로 자료 제출 거부.", "**조세 조약** 상 이중과세 방지 및 **MAP** 신청 압박.", "모든 자료 영문 제출, 번역 시간 소요 유도.", "법무팀 동원, 법리 다툼 예고."]
    ),
    Company(
        name="(주)씨엔해운 (C&)", size="대기업", revenue=12_000_000, operating_income=600_000, tax_target=1600, team_hp_damage=(25, 45), # 스탯 상향
        description="'**해운 재벌**'로 불리는 오너 운영. **조세피난처 SPC** 이용 및 **선박 거래** 관련 탈루 혐의.",
        real_case_desc="[교육] **선박, 항공기** 등 고가 자산 운용 산업은 **조세피난처**(Tax Haven) **SPC**를 이용한 **역외탈세**가 빈번합니다. **BVI, 파나마, 마셜 군도** 등에 **페이퍼컴퍼니**를 세우고 **용선료 수입** 등을 해당 법인으로 빼돌려 국내 세금을 회피합니다. 또한, **선박 매각** 과정에서 **양도차익**을 축소하거나 해외에서 은닉하는 경우도 많습니다. **국제거래조사국**의 주요 타겟입니다.",
        tactics=[
            EvasionTactic("역외탈세 (SPC 이용 용선료)", "**마셜 군도** 등에 설립한 다수 **SPC** 명의로 선박 운용, 국내 발생 **용선료 수입** 1조원 이상을 해외로 빼돌려 은닉.", 1000, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.REVENUE),
            EvasionTactic("선박 매각 차익 은닉", "**노후 선박**을 해외 SPC에 **장부가액 수준**으로 저가 양도 후, 해당 SPC가 제3자에게 **시가**로 고가 매각하는 방식으로 **양도 차익** 600억원 해외 은닉.", 600, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.CAPITAL) # 금액 상향
        ], defense_actions=["해외 법인 대표 연락 두절 주장.", "선박 관련 **이면 계약서** 존재 첩보.", "**해외 로펌** 선임, '현지 법률 검토 필요' 주장하며 시간 끌기.", "정관계 로비 통한 조사 외압 시도."]
    ),
]

# --- 3. 게임 상태 초기화 및 관리 ---
def initialize_game(chosen_lead: TaxManCard, chosen_artifact: Artifact):
    seed = st.session_state.get('seed', 0); random.seed(seed if seed != 0 else None)
    if seed != 0: st.toast(f"ℹ️ RNG 시드 {seed} 고정됨.")
    team_members = [chosen_lead]; all_mem = list(TAX_MAN_DB.values()); remain = [m for m in all_mem if m != chosen_lead]; team_members.extend(random.sample(remain, min(2, len(remain)))); st.session_state.player_team = team_members
    start_deck = [LOGIC_CARD_DB["basic_01"]]*3 + [LOGIC_CARD_DB["basic_02"]]*2 + [LOGIC_CARD_DB["b_tier_04"]]*2 + [LOGIC_CARD_DB["c_tier_02"]]*2 + [LOGIC_CARD_DB["c_tier_01"]]*5 # 14장
    st.session_state.player_deck = random.sample(start_deck, len(start_deck)); st.session_state.player_hand=[]; st.session_state.player_discard=[]
    st.session_state.player_artifacts=[chosen_artifact]
    st.session_state.team_max_hp=sum(m.hp for m in team_members); st.session_state.team_hp=st.session_state.team_max_hp
    st.session_state.player_focus_max=sum(m.focus for m in team_members); st.session_state.player_focus_current=st.session_state.player_focus_max
    st.session_state.team_stats={"analysis":sum(m.analysis for m in team_members),"persuasion":sum(m.persuasion for m in team_members),"evidence":sum(m.evidence for m in team_members),"data":sum(m.data for m in team_members)}
    for art in st.session_state.player_artifacts:
        if art.effect["type"]=="on_battle_start":
            if art.effect["subtype"]=="stat_evidence": st.session_state.team_stats["evidence"]+=art.effect["value"]
            elif art.effect["subtype"]=="stat_persuasion": st.session_state.team_stats["persuasion"]+=art.effect["value"]
    st.session_state.current_battle_company=None; st.session_state.battle_log=[]; st.session_state.selected_card_index=None; st.session_state.bonus_draw=0; st.session_state.company_order=random.sample(COMPANY_DB, len(COMPANY_DB)); st.session_state.game_state="MAP"; st.session_state.current_stage_level=0; st.session_state.total_collected_tax=0

# --- 4. 게임 로직 함수 ---

def start_player_turn():
    focus = sum(m.focus for m in st.session_state.player_team); st.session_state.player_focus_current=focus
    if "임향수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current+=1; log_message("✨ [기획 조사] 집중력 +1!", "info")
    for art in st.session_state.player_artifacts:
        if art.effect["type"]=="on_turn_start" and art.effect["subtype"]=="focus":
            st.session_state.player_focus_current+=art.effect["value"]; log_message(f"✨ {art.name} 집중력 +{art.effect['value']}!", "info")
    st.session_state.player_focus_max = st.session_state.player_focus_current
    if "김대지" in [m.name for m in st.session_state.player_team] and st.session_state.team_stats["data"]>=50 and not st.session_state.get('kim_dj_effect_used', False):
        new=copy.deepcopy(LOGIC_CARD_DB["b_tier_01"]); new.just_created=True; st.session_state.player_hand.append(new);
        log_message("✨ [부동산 조사] '금융거래 분석' 1장 획득!", "info"); st.session_state.kim_dj_effect_used=True
    st.session_state.cost_reduction_active = "전진" in [m.name for m in st.session_state.player_team];
    if st.session_state.cost_reduction_active: log_message("✨ [실무 지휘] 다음 카드 비용 -1!", "info")
    draw_n = 4 + st.session_state.get('bonus_draw', 0)
    if st.session_state.get('bonus_draw', 0)>0:
        log_message(f"✨ 조사계획서 효과로 카드 {st.session_state.bonus_draw}장 추가 드로우!", "info") # 아티팩트 이름 직접 사용
        st.session_state.bonus_draw=0
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
        # 수정: 인덱스 유효성 검사 강화
        if idx < len(st.session_state.player_hand):
            card = st.session_state.player_hand.pop(idx); st.session_state.player_discard.append(card); val = card.special_effect.get('value', 0); log_message(f"✨ [{card.name}] 효과! 카드 {val}장 뽑기.", "info")
            if "조용규" in [m.name for m in st.session_state.player_team] and card.name=="법령 재검토":
                log_message("✨ [세법 교본] +1장 추가!", "info")
                val*=2
            total_draw += val
        else: log_message(f"경고: 드로우 처리 인덱스 오류 (idx: {idx})", "error")
    # 수정: 모든 카드의 just_created 플래그 리셋
    for card in st.session_state.player_hand:
        if hasattr(card, 'just_created'):
            card.just_created=False
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

def calculate_card_cost(card): # SyntaxError 수정됨
    cost = card.cost
    if "백용호" in [m.name for m in st.session_state.player_team] and ('데이터' in card.name or '분석' in card.name or AttackCategory.CAPITAL in card.attack_category):
        cost = max(0, cost - 1)
    is_first = st.session_state.get('turn_first_card_played', True);
    type_match = ('분석' in card.name or '판례' in card.name or '법령' in card.name or AttackCategory.COMMON in card.attack_category)
    if "박지연" in [m.name for m in st.session_state.player_team] and is_first and type_match:
        cost = max(0, cost - 1)
    if "안원구" in [m.name for m in st.session_state.player_team] and card.name in ['현장 압수수색', '차명계좌 추적']:
        cost = max(0, cost - 1)
    if st.session_state.get('cost_reduction_active', False):
        original_cost = cost
        cost = max(0, cost - 1)
        if cost < original_cost:
            st.session_state.cost_reduction_active = False
            log_message(f"✨ [실무 지휘] 카드 비용 -1!", "info")
    for art in st.session_state.player_artifacts:
        if art.effect["type"] == "on_cost_calculate" and card.name in art.effect["target_cards"]:
            cost = max(0, cost + art.effect["value"])
    return cost

def execute_attack(card_index, tactic_index): # SyntaxError 수정됨, 로그 강화
    # ... (입력값 검증, 카드/전술/회사 객체 가져오기 - 이전과 동일)
    if card_index is None or card_index >= len(st.session_state.player_hand):
        st.toast("오류: 잘못된 카드 인덱스.", icon="🚨"); st.session_state.selected_card_index = None; st.rerun(); return

    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    company = st.session_state.current_battle_company

    # [수정] 잔여 혐의 처리: tactic_index가 실제 혐의 범위를 벗어나면 잔여 혐의로 간주
    is_residual = tactic_index >= len(company.tactics)
    tactic = ResidualTactic() if is_residual else company.tactics[tactic_index]

    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); st.session_state.selected_card_index = None; st.rerun(); return

    # --- 페널티 체크 (잔여 혐의는 항상 통과) ---
    is_tax = is_residual or (TaxType.COMMON in card.tax_type) or (isinstance(tactic.tax_type, list) and any(tt in card.tax_type for tt in tactic.tax_type)) or (tactic.tax_type in card.tax_type)
    if not is_tax:
        t_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value];
        log_message(f"❌ [세목 불일치!] '{card.name}' -> '{', '.join(t_types)}' (❤️-10)", "error"); st.session_state.team_hp -= 10;
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return
    is_cat = is_residual or (AttackCategory.COMMON in card.attack_category) or (tactic.tactic_category in card.attack_category)
    if not is_cat:
        log_message(f"🚨 [유형 불일치!] '{card.name}' -> '{tactic.tactic_category.value}' ({tactic.name}) (❤️-5)", "error"); st.session_state.team_hp -= 5;
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return

    # --- 비용 지불 ---
    st.session_state.player_focus_current -= cost;
    if st.session_state.get('turn_first_card_played', True): st.session_state.turn_first_card_played = False

    # --- 데미지 계산 ---
    base = card.base_damage; ref = 500; scale = (company.tax_target / ref)**0.5 if company.tax_target > 0 else 0.5; capped = max(0.5, min(2.0, scale)); scaled = int(base * capped); scale_log = f" (규모 보정: {base}→{scaled})" if capped != 1.0 else ""; damage = scaled
    team_stats = st.session_state.team_stats; team_bonus = 0
    # ... (팀 스탯, 조사관 능력 보너스 - 이전과 동일)
    if any(c in [AttackCategory.COST, AttackCategory.COMMON] for c in card.attack_category): team_bonus += int(team_stats["analysis"] * 0.5)
    if AttackCategory.CAPITAL in card.attack_category: team_bonus += int(team_stats["data"] * 1.0)
    if '판례' in card.name: team_bonus += int(team_stats["persuasion"] * 1.0)
    if '압수' in card.name: team_bonus += int(team_stats["evidence"] * 1.5)
    if team_bonus > 0: log_message(f"📈 [팀 스탯 +{team_bonus}]", "info"); damage += team_bonus
    if "이철수" in [m.name for m in st.session_state.player_team] and card.name in ["기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]: damage += 8; log_message("✨ [기본기] +8!", "info")
    if "임향수" in [m.name for m in st.session_state.player_team] and ('분석' in card.name or '자료' in card.name or '추적' in card.name or AttackCategory.CAPITAL in card.attack_category): bonus = int(team_stats["analysis"] * 0.1 + team_stats["data"] * 0.1); damage += bonus; log_message(f"✨ [기획 조사] +{bonus}!", "info")
    if "유재준" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.ERROR:
        bonus = int(team_stats["persuasion"] / 10)
        if bonus > 0: damage += bonus; log_message(f"✨ [정기 조사] +{bonus}!", "info")
    if "김태호" in [m.name for m in st.session_state.player_team] and AttackCategory.CAPITAL in card.attack_category:
        bonus = int(team_stats["evidence"] * 0.1)
        if bonus > 0: damage += bonus; log_message(f"✨ [심층 기획] +{bonus}!", "info")

    # --- 최종 피해 배율 ---
    mult = 1.0; mult_log = ""
    # 잔여 혐의는 보너스 배율 없음
    if not is_residual and card.special_bonus and card.special_bonus.get('target_method') == tactic.method_type:
        m = card.special_bonus.get('multiplier', 1.0); mult *= m; mult_log += f"🔥[{card.special_bonus.get('bonus_desc')}] "
        if "조용규" in [m.name for m in st.session_state.player_team] and card.name == "판례 제시": mult *= 2; mult_log += "✨[세법 교본 x2] "
    if "한중히" in [m.name for m in st.session_state.player_team] and (company.size == "외국계" or tactic.method_type == MethodType.CAPITAL_TX): mult *= 1.3; mult_log += "✨[역외탈세 +30%] "
    if "서영택" in [m.name for m in st.session_state.player_team] and (company.size == "대기업" or company.size == "외국계") and TaxType.CORP in card.tax_type: mult *= 1.25; mult_log += "✨[대기업 +25%] "
    if "이현동" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.INTENTIONAL: mult *= 1.2; mult_log += "✨[지하경제 +20%] "
    final_dmg = int(damage * mult)

    # --- 오버킬 및 세액 계산 ---
    if is_residual: # 잔여 혐의는 오버킬 없음
        dmg_tactic = final_dmg
        overkill = 0
        overkill_contrib = 0
        tactic.exposed_amount += dmg_tactic # 필요 없을 수 있지만, 일관성을 위해
    else: # 기존 혐의
        remain = tactic.total_amount - tactic.exposed_amount; dmg_tactic = min(final_dmg, remain);
        overkill = final_dmg - dmg_tactic; overkill_contrib = int(overkill * 0.5);
        tactic.exposed_amount += dmg_tactic;

    company.current_collected_tax += (dmg_tactic + overkill_contrib)

    # --- 로그 강화 ---
    log_prefix = "▶️ [적중]" if mult <= 1.0 else ("💥 [치명타!]" if mult >= 2.0 else "👍 [효과적!]")
    target_name = tactic.name if tactic else "[알 수 없는 혐의]"
    log_message(f"{log_prefix} '{card.name}' → '{target_name}'에 **{final_dmg}억원** 피해!{scale_log}", "success")
    if mult_log: log_message(f" ㄴ {mult_log}", "info")

    # 카드별/상황별 추가 로그
    if card.name == "금융거래 분석": log_message(f"💬 금융 분석팀: 의심스러운 자금 흐름 포착!", "info")
    elif card.name == "차명계좌 추적": log_message(f"💬 조사팀: 은닉 계좌 추적 성공! 자금 흐름 확보!", "warning")
    elif card.name == "현장 압수수색": log_message(f"💬 현장팀: 압수수색으로 결정적 증거물 확보!", "warning")
    elif card.name == "자금출처조사": log_message(f"💬 조사팀: 자금 출처 소명 요구, 압박 수위 높임!", "info")
    elif tactic.method_type == MethodType.INTENTIONAL and final_dmg > tactic.total_amount * 0.5 and not is_residual: log_message(f"💬 조사팀: 고의적 탈루 정황 가중! 추가 조사 필요.", "warning")
    elif tactic.method_type == MethodType.ERROR and '판례' in card.name: log_message(f"💬 법무팀: 유사 판례 제시하여 납세자 설득 중...", "info")
    elif tactic.method_type == MethodType.CAPITAL_TX: log_message(f"💬 분석팀: 복잡한 자본 거래 구조 분석 완료.", "info")
    if final_dmg < 10 and damage > 0: log_message(f"💬 조사관: 꼼꼼하게 증빙 대조하며 조금씩 밝혀냅니다.", "info")
    elif final_dmg > 100: log_message(f"💬 조사팀장: 결정적인 증거입니다! 큰 타격을 입혔습니다!", "success")

    if overkill > 0: log_message(f"📈 [초과 기여] 혐의 초과 데미지 {overkill}억 중 {overkill_contrib}억원을 추가 세액으로 확보!", "info")

    # --- 혐의 완료 처리 (잔여 혐의 제외) ---
    if not is_residual and tactic.exposed_amount >= tactic.total_amount and not getattr(tactic, '_logged_clear', False): # 중복 로그 방지
        # tactic.is_cleared = True # EvasionTactic 객체에 직접 상태 변경
        setattr(tactic, 'is_cleared', True) # ResidualTactic 회피
        setattr(tactic, '_logged_clear', True) # 로그 중복 방지 플래그
        log_message(f"🔥 [{tactic.name}] 혐의 완전 적발 완료! (총 {tactic.total_amount}억원)", "warning")
        if "벤츠" in card.text: log_message("💬 [현장] 법인소유 벤츠 키 확보!", "info")
        if "압수수색" in card.name: log_message("💬 [현장] 비밀장부 및 관련 증거물 다수 확보!", "info")

    # --- 마무리 ---
    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None;
    check_battle_end(); st.rerun()

# --- [수정됨] 자동 공격 로직 개선 ---
def execute_auto_attack():
    affordable_attacks = []
    # 1. 사용 가능한 모든 공격 카드 찾기 (유틸 제외)
    for i, card in enumerate(st.session_state.player_hand):
        if card.base_damage <= 0 or (card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]):
            continue
        cost = calculate_card_cost(card)
        if st.session_state.player_focus_current >= cost:
            affordable_attacks.append({'card': card, 'index': i, 'cost': cost})

    # 2. 공격력 높은 순으로 정렬
    affordable_attacks.sort(key=lambda x: x['card'].base_damage, reverse=True)

    if not affordable_attacks:
        st.toast("⚡ 사용할 수 있는 자동 공격 카드가 없습니다.", icon="⚠️"); return

    # 3. 가장 강한 카드부터 순서대로 유효 타겟 검색 및 공격
    company = st.session_state.current_battle_company
    attack_executed = False
    all_tactics_cleared = all(t.is_cleared for t in company.tactics)

    for attack_info in affordable_attacks:
        current_card = attack_info['card']
        current_idx = attack_info['index']
        target_idx = -1

        # 먼저 실제 혐의 중 공격 가능한 것 찾기
        if not all_tactics_cleared:
            for i, t in enumerate(company.tactics):
                if t.is_cleared: continue
                is_tax = (TaxType.COMMON in current_card.tax_type) or (isinstance(t.tax_type, list) and any(tt in current_card.tax_type for tt in t.tax_type)) or (t.tax_type in current_card.tax_type)
                is_cat = (AttackCategory.COMMON in current_card.attack_category) or (t.tactic_category in current_card.attack_category)
                if is_tax and is_cat:
                    target_idx = i; break

        # 실제 혐의 공격 못하면 잔여 혐의 공격 시도 (모든 혐의 클리어 시)
        if target_idx == -1 and all_tactics_cleared and company.current_collected_tax < company.tax_target:
             # 잔여 혐의는 COMMON 타입이므로 모든 카드가 공격 가능
             target_idx = len(company.tactics) # 잔여 혐의 인덱스 (가상)

        if target_idx != -1:
            target_name = "[잔여 혐의 조사]" if target_idx >= len(company.tactics) else company.tactics[target_idx].name
            log_message(f"⚡ 자동 공격: '{current_card.name}' -> '{target_name}'!", "info")
            execute_attack(current_idx, target_idx)
            attack_executed = True
            break # 공격 성공 시 루프 종료

    if not attack_executed:
        st.toast(f"⚡ 현재 손패의 카드로 공격 가능한 혐의가 없습니다.", icon="⚠️")


def end_player_turn():
    # 플래그 리셋 등
    if 'kim_dj_effect_used' in st.session_state: st.session_state.kim_dj_effect_used = False
    if 'cost_reduction_active' in st.session_state: st.session_state.cost_reduction_active = False
    # 손패 버리기
    st.session_state.player_discard.extend(st.session_state.player_hand); st.session_state.player_hand = []; st.session_state.selected_card_index = None
    log_message("--- 기업 턴 시작 ---"); enemy_turn()
    # 게임 종료 체크 후 플레이어 턴 시작 또는 게임 종료
    if not check_battle_end():
        start_player_turn()
        st.rerun()

def enemy_turn():
    co = st.session_state.current_battle_company; act = random.choice(co.defense_actions); min_d, max_d = co.team_hp_damage; dmg = random.randint(min_d, max_d); st.session_state.team_hp -= dmg
    prefix = "◀️ [기업]" if not (co.size in ["대기업", "외국계"] and "로펌" in act) else "◀️ [로펌]"; log_message(f"{prefix} {act} (팀 사기 저하 ❤️-{dmg}!)", "error")

def check_battle_end(): # SyntaxError 수정됨
    company = st.session_state.current_battle_company
    if company.current_collected_tax >= company.tax_target:
        bonus = company.current_collected_tax - company.tax_target
        log_message(f"🎉 [조사 승리] 목표 {company.tax_target:,}억원 달성! (초과 {bonus:,}억원)", "success")
        st.session_state.total_collected_tax += company.current_collected_tax
        st.session_state.game_state = "REWARD"
        if st.session_state.player_discard:
            # 수정: IndexError 방지
            try:
                last_card_text = st.session_state.player_discard[-1].text
                st.toast(f"승리! \"{last_card_text}\"", icon="🎉")
            except IndexError:
                st.toast("승리!", icon="🎉") # 버린 덱이 비어있을 경우
        else:
             st.toast("승리!", icon="🎉")
        return True
    if st.session_state.team_hp <= 0:
        st.session_state.team_hp = 0
        log_message("‼️ [조사 중단] 팀 체력 소진...", "error")
        st.session_state.game_state = "GAME_OVER"
        return True
    return False

def start_battle(co_template): # SyntaxError 수정됨
    co = copy.deepcopy(co_template); st.session_state.current_battle_company = co; st.session_state.game_state = "BATTLE"; st.session_state.battle_log = [f"--- {co.name} ({co.size}) 조사 시작 ---"]
    log_message(f"🏢 **{co.name}** 주요 탈루 혐의:", "info"); t_types = set();
    for t in co.tactics: tax = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value]; log_message(f"- **{t.name}** ({'/'.join(tax)}, {t.method_type.value}, {t.tactic_category.value})", "info"); t_types.add(t.method_type)
    log_message("---", "info"); guide = "[조사 가이드] "; has_g = False
    if MethodType.INTENTIONAL in t_types: guide += "고의 탈루: 증거 확보, 압박 중요. "; has_g = True
    if MethodType.CAPITAL_TX in t_types or co.size in ["대기업", "외국계"]: guide += "자본/국제 거래: 자금 흐름, 법규 분석 필요. "; has_g = True
    if MethodType.ERROR in t_types and MethodType.INTENTIONAL not in t_types: guide += "단순 오류: 규정/판례 제시, 설득 효과적. "; has_g = True
    log_message(guide if has_g else "[조사 가이드] 기업 특성/혐의 고려, 전략적 접근.", "warning"); log_message("---", "info")
    st.session_state.bonus_draw = 0
    for art in st.session_state.player_artifacts:
        log_message(f"✨ [조사도구] '{art.name}' 효과 준비.", "info")
        if art.effect["type"] == "on_battle_start" and art.effect["subtype"] == "draw":
            st.session_state.bonus_draw += art.effect["value"]
    st.session_state.player_deck.extend(st.session_state.player_discard); st.session_state.player_deck = random.sample(st.session_state.player_deck, len(st.session_state.player_deck)); st.session_state.player_discard = []; st.session_state.player_hand = []; start_player_turn()

def log_message(message, level="normal"):
    color = {"success": "green", "warning": "orange", "error": "red", "info": "blue"}.get(level)
    msg = f":{color}[{message}]" if color else message; st.session_state.battle_log.insert(0, msg)
    if len(st.session_state.battle_log) > 50: st.session_state.battle_log.pop()

def go_to_next_stage(add_card=None, heal_amount=0):
    if add_card: st.session_state.player_deck.append(add_card); st.toast(f"[{add_card.name}] 덱 추가!", icon="🃏")
    if heal_amount > 0: st.session_state.team_hp = min(st.session_state.team_max_hp, st.session_state.team_hp + heal_amount); st.toast(f"팀 휴식 (체력 +{heal_amount})", icon="❤️")
    if 'reward_cards' in st.session_state: del st.session_state.reward_cards
    st.session_state.game_state = "MAP"; st.session_state.current_stage_level += 1; st.rerun()

# --- 5. UI 화면 함수 --- (이하 동일, 리스트 컴프리헨션 -> for loop 수정)

def show_main_menu():
    st.title("💼 세무조사: 덱빌딩 로그라이크"); st.markdown("---"); st.header("국세청에 오신 것을 환영합니다.")
    st.markdown("당신은 오늘부로 세무조사팀에 발령받았습니다..."); st.image("...", caption="국세청 전경", width=400)
    st.session_state.seed = st.number_input("RNG 시드 (0 = 랜덤)", value=0, step=1, help="동일 시드로 반복 테스트 가능")
    if st.button("🚨 조사 시작", type="primary", use_container_width=True):
        seed = st.session_state.get('seed', 0); random.seed(seed if seed != 0 else None)
        members = list(TAX_MAN_DB.values()); st.session_state.draft_team_choices = random.sample(members, min(len(members), 3))
        artifacts = list(ARTIFACT_DB.keys()); chosen_keys = random.sample(artifacts, min(len(artifacts), 3)); st.session_state.draft_artifact_choices = [ARTIFACT_DB[k] for k in chosen_keys]
        st.session_state.game_state = "GAME_SETUP_DRAFT"; st.rerun()
    with st.expander("📖 게임 방법", expanded=True): st.markdown("""**1.🎯 목표**: ...\n**2.⚔️ 전투**: ...\n**3.⚠️ 패널티**: ...\n**4.✨ 보너스**: ...""")

def show_setup_draft_screen():
    st.title("👨‍💼 조사팀 구성"); st.markdown("팀 **리더**와 시작 **조사도구** 선택:")
    if 'draft_team_choices' not in st.session_state or 'draft_artifact_choices' not in st.session_state: st.error("드래프트 정보 없음..."); st.button("메인 메뉴로", on_click=lambda: st.session_state.update(game_state="MAIN_MENU")); return
    teams = st.session_state.draft_team_choices; arts = st.session_state.draft_artifact_choices
    st.markdown("---"); st.subheader("1. 팀 리더 선택:"); lead_idx = st.radio("리더", range(len(teams)), format_func=lambda i: f"**{teams[i].name} ({teams[i].grade}급)** | {teams[i].description}\n   └ **{teams[i].ability_name}**: {teams[i].ability_desc}", label_visibility="collapsed")
    st.markdown("---"); st.subheader("2. 시작 조사도구 선택:"); art_idx = st.radio("도구", range(len(arts)), format_func=lambda i: f"**{arts[i].name}** | {arts[i].description}", label_visibility="collapsed")
    st.markdown("---");
    if st.button("이 구성으로 조사 시작", type="primary", use_container_width=True):
        initialize_game(teams[lead_idx], arts[art_idx])
        del st.session_state.draft_team_choices, st.session_state.draft_artifact_choices
        st.rerun()

def show_map_screen():
    if 'current_stage_level' not in st.session_state: st.warning("게임 상태 초기화됨..."); st.session_state.game_state = "MAIN_MENU"; st.rerun(); return
    st.header(f"📍 조사 지역 (Stage {st.session_state.current_stage_level + 1})"); st.write("조사할 기업 선택:")
    companies = st.session_state.company_order
    if st.session_state.current_stage_level < len(companies):
        co = companies[st.session_state.current_stage_level]
        with st.container(border=True):
            st.subheader(f"🏢 {co.name} ({co.size})"); st.markdown(co.description)
            c1, c2 = st.columns(2); c1.metric("매출액", format_krw(co.revenue)); c2.metric("영업이익", format_krw(co.operating_income))
            st.warning(f"**예상 턴당 데미지:** {co.team_hp_damage[0]}~{co.team_hp_damage[1]} ❤️"); st.info(f"**목표 추징 세액:** {co.tax_target:,} 억원 💰")
            with st.expander("🔍 혐의 및 실제 사례 정보 보기"):
                st.markdown("---"); st.markdown("### 📚 실제 사례 기반 교육 정보"); st.markdown(co.real_case_desc)
                st.markdown("---"); st.markdown("### 📝 주요 탈루 혐의 분석")
                for t in co.tactics:
                    t_types = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value];
                    st.markdown(f"**📌 {t.name}** (`{'/'.join(t_types)}`, `{t.method_type.value}`, `{t.tactic_category.value}`)\n> _{t.description}_")
            if st.button(f"🚨 {co.name} 조사 시작", type="primary", use_container_width=True):
                start_battle(co)
                st.rerun()
    else:
        st.success("🎉 모든 기업 조사 완료!"); st.balloons();
        st.button("🏆 다시 시작", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"))

def show_battle_screen(): # 잔여 혐의 표시 로직 추가
    if not st.session_state.current_battle_company: st.error("오류: 기업 정보 없음..."); st.session_state.game_state = "MAP"; st.rerun(); return
    co = st.session_state.current_battle_company; st.title(f"⚔️ {co.name} 조사 중..."); st.markdown("---")
    col_co, col_log, col_hand = st.columns([1.6, 2.0, 1.4])
    with col_co:
        st.subheader(f"🏢 {co.name} ({co.size})"); st.progress(min(1.0, co.current_collected_tax/co.tax_target if co.tax_target > 0 else 1.0), text=f"💰 목표 세액: {co.current_collected_tax:,}/{co.tax_target:,} (억원)"); st.markdown("---"); st.subheader("🧾 탈루 혐의 목록")
        is_sel = st.session_state.get("selected_card_index") is not None
        if is_sel: st.info(f"**'{st.session_state.player_hand[st.session_state.selected_card_index].name}'** 카드로 공격할 혐의 선택:")

        # [수정] 모든 혐의 클리어 여부 확인
        all_tactics_cleared = all(t.is_cleared for t in co.tactics)
        target_not_met = co.current_collected_tax < co.tax_target

        tactic_cont = st.container(height=450)
        with tactic_cont:
            # 모든 혐의 클리어했고 목표 미달 시 잔여 혐의 표시
            if all_tactics_cleared and target_not_met:
                residual_tactic = ResidualTactic()
                with st.container(border=True):
                    st.markdown(f"**{residual_tactic.name}** (`공통`, `단순 오류`, `공통`)")
                    st.markdown(f"*{residual_tactic.description}*")
                    remaining_tax = co.tax_target - co.current_collected_tax
                    st.progress(0.0, text=f"남은 추징 목표: {remaining_tax:,}억원")
                    if is_sel:
                         card = st.session_state.player_hand[st.session_state.selected_card_index]
                         # 잔여 혐의는 항상 공격 가능
                         if st.button(f"🎯 **{residual_tactic.name}** 공격", key=f"attack_residual", use_container_width=True, type="primary"):
                             execute_attack(st.session_state.selected_card_index, len(co.tactics)) # 가상 인덱스 전달

            # 그렇지 않으면 기존 혐의 목록 표시
            elif not co.tactics: st.write("(조사할 특정 혐의 없음)")
            else:
                for i, t in enumerate(co.tactics):
                    cleared = t.is_cleared # 실제 is_cleared 사용
                    with st.container(border=True):
                        t_types = [tx.value for tx in t.tax_type] if isinstance(t.tax_type, list) else [t.tax_type.value]; st.markdown(f"**{t.name}** (`{'/'.join(t_types)}`/`{t.method_type.value}`/`{t.tactic_category.value}`)\n*{t.description}*")
                        prog_txt = f"✅ 완료: {t.total_amount:,}억" if cleared else f"적발: {t.exposed_amount:,}/{t.total_amount:,}억"; st.progress(1.0 if cleared else (min(1.0, t.exposed_amount/t.total_amount) if t.total_amount > 0 else 1.0), text=prog_txt)
                        if is_sel and not cleared:
                            card = st.session_state.player_hand[st.session_state.selected_card_index]
                            is_tax = (TaxType.COMMON in card.tax_type) or (isinstance(t.tax_type, list) and any(tt in card.tax_type for tt in t.tax_type)) or (t.tax_type in card.tax_type)
                            is_cat = (AttackCategory.COMMON in card.attack_category) or (t.tactic_category in card.attack_category)
                            label, type, help = f"🎯 **{t.name}** 공격", "primary", "클릭하여 공격!"
                            if card.special_bonus and card.special_bonus.get('target_method') == t.method_type: label = f"💥 [특효!] **{t.name}** 공격"; help = f"클릭! ({card.special_bonus.get('bonus_desc')})"
                            disabled = False
                            if not is_tax: label, type, help, disabled = f"⚠️ (세목 불일치!) {t.name}", "secondary", f"세목 불일치! ... (❤️-10)", True
                            elif not is_cat: label, type, help, disabled = f"⚠️ (유형 불일치!) {t.name}", "secondary", f"유형 불일치! ... (❤️-5)", True
                            if st.button(label, key=f"attack_{i}", use_container_width=True, type=type, disabled=disabled, help=help):
                                execute_attack(st.session_state.selected_card_index, i)
    with col_log:
        st.subheader("❤️ 팀 현황"); c1, c2 = st.columns(2); c1.metric("팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}"); c2.metric("현재 집중력", f"{st.session_state.player_focus_current}/{st.session_state.player_focus_max}")
        if st.session_state.get('cost_reduction_active', False): st.info("✨ [실무 지휘] 다음 카드 비용 -1"); st.markdown("---")
        st.subheader("📋 조사 기록 (로그)"); log_cont = st.container(height=300, border=True);
        for log in st.session_state.battle_log: # 수정: for loop
            log_cont.markdown(log)
        st.markdown("---"); st.subheader("🕹️ 행동")
        if st.session_state.get("selected_card_index") is not None: st.button("❌ 공격 취소", on_click=cancel_card_selection, use_container_width=True, type="secondary")
        else: act_cols = st.columns(2); act_cols[0].button("➡️ 턴 종료", on_click=end_player_turn, use_container_width=True, type="primary"); act_cols[1].button("⚡ 자동 공격", on_click=execute_auto_attack, use_container_width=True, type="secondary", help="가장 강력하고 사용 가능한 카드로 첫 번째 유효 혐의 자동 공격.")
    with col_hand:
        st.subheader(f"🃏 손패 ({len(st.session_state.player_hand)})")
        if not st.session_state.player_hand: st.write("(손패 없음)")
        for i, card in enumerate(st.session_state.player_hand):
            if i >= len(st.session_state.player_hand): continue
            cost = calculate_card_cost(card); afford = st.session_state.player_focus_current >= cost; color = "blue" if afford else "red"; selected = (st.session_state.get("selected_card_index") == i)
            with st.container(border=True):
                title = f"**{card.name}** | :{color}[비용: {cost} 🧠]" + (" (선택됨)" if selected else ""); st.markdown(title)
                c_types=[t.value for t in card.tax_type]; c_cats=[c.value for c in card.attack_category]; st.caption(f"세목:`{'`,`'.join(c_types)}`|유형:`{'`,`'.join(c_cats)}`"); st.markdown(card.description)
                if card.base_damage > 0: st.markdown(f"**기본 적출액:** {card.base_damage} 억원")
                if card.special_bonus: st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")
                btn_label = f"선택: {card.name}"
                if card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]: btn_label = f"사용: {card.name}"
                disabled = not afford; help = f"집중력 부족! ({cost})" if not afford else None
                if st.button(btn_label, key=f"play_{i}", use_container_width=True, disabled=disabled, help=help):
                    select_card_to_play(i)

def show_reward_screen(): # SyntaxError 수정됨
    st.header("🎉 조사 승리!"); st.balloons(); co = st.session_state.current_battle_company; st.success(f"**{co.name}** 조사 완료. 총 {co.current_collected_tax:,}억원 추징."); st.markdown("---")
    t1, t2, t3 = st.tabs(["🃏 카드 획득 (택1)", "❤️ 팀 정비", "🗑️ 덱 정비"])
    with t1:
        st.subheader("🎁 획득할 카드 1장 선택")
        if 'reward_cards' not in st.session_state or not st.session_state.reward_cards:
            pool = [c for c in LOGIC_CARD_DB.values() if not (c.cost == 0 and c.special_effect and c.special_effect.get("type") == "draw")]
            opts = []; has_cap = any(t.method_type == MethodType.CAPITAL_TX for t in co.tactics)
            if has_cap:
                cap_cards = [c for c in pool if AttackCategory.CAPITAL in c.attack_category and c not in opts]
                if cap_cards:
                    opts.append(random.choice(cap_cards))
                    st.toast("ℹ️ [보상 가중치] '자본' 카드 1장 포함!")
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
                    types=[t.value for t in card.tax_type]; cats=[c.value for c in card.attack_category]; st.markdown(f"**{card.name}**|비용:{card.cost}🧠"); st.caption(f"세목:`{'`,`'.join(types)}`|유형:`{'`,`'.join(cats)}`"); st.markdown(card.description);
                    if card.base_damage > 0: st.info(f"**기본 적출액:** {card.base_damage} 억원")
                    elif card.special_effect and card.special_effect.get("type") == "draw": st.info(f"**드로우:** +{card.special_effect.get('value', 0)}")
                    if card.special_bonus: st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")
                    if st.button(f"선택: {card.name}", key=f"reward_{i}", use_container_width=True, type="primary"):
                        go_to_next_stage(add_card=card)
    with t2:
        st.subheader("❤️ 팀 체력 회복"); st.markdown(f"현재: {st.session_state.team_hp}/{st.session_state.team_max_hp}"); heal=int(st.session_state.team_max_hp*0.3);
        st.button(f"팀 정비 (+{heal} 회복)", on_click=go_to_next_stage, kwargs={'heal_amount': heal}, use_container_width=True)
    with t3:
        st.subheader("🗑️ 덱에서 기본 카드 1장 제거"); st.markdown("덱 압축으로 좋은 카드 뽑을 확률 증가.");
        st.info("제거 대상: '단순 자료 대사', '기본 경비 적정성 검토', '단순 경비 처리 오류 지적'");
        st.button("기본 카드 제거하러 가기", on_click=lambda: st.session_state.update(game_state="REWARD_REMOVE"), use_container_width=True)

def show_reward_remove_screen():
    st.header("🗑️ 덱 정비 (카드 제거)"); st.markdown("제거할 기본 카드 1장 선택:")
    deck = st.session_state.player_deck + st.session_state.player_discard; basics = ["단순 자료 대사", "기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]
    removable = {name: card for card in deck if card.name in basics and card.name not in locals().get('removable', {})}
    if not removable:
        st.warning("제거 가능한 기본 카드 없음."); st.button("맵으로 돌아가기", on_click=go_to_next_stage); return
    cols = st.columns(len(removable))
    for i, (name, card) in enumerate(removable.items()):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{card.name}** | 비용: {card.cost} 🧠"); st.markdown(card.description)
                if st.button(f"제거: {card.name}", key=f"remove_{i}", use_container_width=True, type="primary"):
                    msg = ""; found = False
                    try: st.session_state.player_deck.remove(next(c for c in st.session_state.player_deck if c.name == name)); msg = "덱"; found = True
                    except (StopIteration, ValueError):
                        try: st.session_state.player_discard.remove(next(c for c in st.session_state.player_discard if c.name == name)); msg = "버린 덱"; found = True
                        except (StopIteration, ValueError): st.error("오류: 카드 제거 실패.")
                    if found:
                        st.toast(f"{msg}에서 [{name}] 1장 제거!", icon="🗑️")
                        go_to_next_stage()
                        return
    st.markdown("---"); st.button("제거 취소 (맵으로)", on_click=go_to_next_stage, type="secondary")

def show_game_over_screen():
    st.header("... 조사 중단 ..."); st.error("팀 체력 소진.")
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax:,} 억원"); st.metric("진행 스테이지", f"📍 {st.session_state.current_stage_level + 1}")
    st.image("https://images.unsplash.com/photo-1554224155-16954a151120?...", caption="지친 조사관들...", width=400)
    st.button("다시 도전", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), type="primary", use_container_width=True)

def show_player_status_sidebar():
    with st.sidebar:
        st.title("👨‍💼 조사팀 현황"); st.metric("💰 총 추징 세액", f"{st.session_state.total_collected_tax:,} 억원")
        if st.session_state.game_state != "BATTLE":
            st.metric("❤️ 현재 팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}")
        st.markdown("---")
        with st.expander("📊 팀 스탯", expanded=False):
            stats = st.session_state.team_stats; st.markdown(f"- 분석력: {stats['analysis']}\n- 설득력: {stats['persuasion']}\n- 증거력: {stats['evidence']}\n- 데이터: {stats['data']}")
        st.subheader("👥 팀원 (3명)")
        for m in st.session_state.player_team:
             with st.expander(f"**{m.name}** ({m.grade}급)"): st.markdown(f"HP:{m.hp}/{m.max_hp}, Focus:{m.focus}\n**{m.ability_name}**: {m.ability_desc}\n({m.description})")
        st.markdown("---")
        total = len(st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand); st.subheader(f"📚 보유 덱 ({total}장)")
        with st.expander("덱 구성 보기"):
            deck = st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand; counts = {};
            for card in deck: counts[card.name] = counts.get(card.name, 0) + 1
            for name in sorted(counts.keys()): # 수정: for loop
                st.write(f"- {name} x {counts[name]}")
        if st.session_state.game_state == "BATTLE":
            with st.expander("🗑️ 버린 덱 보기"):
                discard_counts = {name: 0 for name in counts};
                for card in st.session_state.player_discard: discard_counts[card.name] = discard_counts.get(card.name, 0) + 1
                if not any(v > 0 for v in discard_counts.values()): st.write("(버린 카드 없음)")
                else: # 수정: for loop
                    for n, c in sorted(discard_counts.items()):
                        if c > 0: st.write(f"- {n} x {c}")
        st.markdown("---"); st.subheader("🧰 보유 도구")
        if not st.session_state.player_artifacts: st.write("(없음)")
        else: # 수정: for loop
            for art in st.session_state.player_artifacts: st.success(f"- {art.name}: {art.description}")
        st.markdown("---"); st.button("게임 포기 (메인 메뉴)", on_click=lambda: st.session_state.update(game_state="MAIN_MENU"), use_container_width=True)

# --- 6. 메인 실행 로직 ---
def main():
    st.set_page_config(page_title="세무조사 덱빌딩", layout="wide", initial_sidebar_state="expanded")
    if 'game_state' not in st.session_state: st.session_state.game_state = "MAIN_MENU"
    running = ["MAP", "BATTLE", "REWARD", "REWARD_REMOVE"]
    if st.session_state.game_state in running and 'player_team' not in st.session_state:
        st.toast("⚠️ 세션 만료, 메인 메뉴로."); st.session_state.game_state = "MAIN_MENU"; st.rerun(); return
    pages = { "MAIN_MENU": show_main_menu, "GAME_SETUP_DRAFT": show_setup_draft_screen, "MAP": show_map_screen, "BATTLE": show_battle_screen, "REWARD": show_reward_screen, "REWARD_REMOVE": show_reward_remove_screen, "GAME_OVER": show_game_over_screen }
    pages[st.session_state.game_state]()
    if st.session_state.game_state not in ["MAIN_MENU", "GAME_OVER", "GAME_SETUP_DRAFT"] and 'player_team' in st.session_state:
        show_player_status_sidebar()

if __name__ == "__main__":
    main()
