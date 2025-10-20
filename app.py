import streamlit as st
import random
import copy  # 기업 객체 복사를 위해

# =============================
# 0) 경량 패치 전략 (약 30% 수용)
# - 게임 플레이 로직은 크게 바꾸지 않고, 고임팩트/저비용 수정만 반영
#   1) "이철수" 시너지 버그 픽스 (카드명 불일치)
#   2) 단위 혼재 완화: 표시 단위 정리(백만원 기준 병기 함수)
#   3) 전술 안전장치: "안전 모드" 토글 시 불일치 공격 버튼 비활성화 + 툴팁
#   4) 포커스 부족/비용 안내 툴팁 추가
#   5) 재현성 옵션: 사이드바 난수 시드 입력 (선택)
#   6) IT기업 교육 텍스트 최신화 (SW 과세 안내)
# =============================

# ---- (A) 전역 설정/유틸 ---------------------------------------------
SAFE_MODE_DEFAULT = False  # 안전 모드 기본값(세목/유형 불일치 공격 차단)

COLOR = {
    "normal": "",
    "success": "green",
    "warning": "orange",
    "error": "red",
    "info": "blue",
}

# 금액 표시에 쓰는 헬퍼: 억원 ↔ 백만원 병기

def to_baekman_from_eok(eok: int) -> int:
    return int(eok) * 100


def both_units_eok_display(eok_value: int) -> str:
    return f"{eok_value:,} 억원 (≈ {to_baekman_from_eok(eok_value):,} 백만원)"


def fmt_baekman(v: int) -> str:
    return f"{v:,} 백만원"


# ---- (B) 기본 데이터 구조 --------------------------------------------
class Card:
    def __init__(self, name, description, cost):
        self.name = name
        self.description = description
        self.cost = cost


class TaxManCard(Card):
    def __init__(
        self,
        name,
        grade_num,
        position,
        description,
        cost,
        hp,
        focus,
        analysis,
        persuasion,
        evidence,
        data,
        ability_name,
        ability_desc,
    ):
        super().__init__(name, description, cost)
        self.grade_num = grade_num
        self.position = position
        self.hp = hp
        self.max_hp = hp
        self.focus = focus
        self.analysis = analysis
        self.persuasion = persuasion
        self.evidence = evidence
        self.data = data
        self.ability_name = ability_name
        self.ability_desc = ability_desc
        grade_map = {4: "S", 5: "S", 6: "A", 7: "B", 8: "C", 9: "C"}
        self.grade = grade_map.get(self.grade_num, "C")


class LogicCard(Card):
    def __init__(
        self,
        name,
        description,
        cost,
        base_damage,
        tax_type,
        attack_category,
        text,
        special_effect=None,
        special_bonus=None,
    ):
        super().__init__(name, description, cost)
        self.base_damage = base_damage
        self.tax_type = tax_type
        self.attack_category = attack_category
        self.text = text
        self.special_effect = special_effect
        self.special_bonus = special_bonus


class EvasionTactic:
    def __init__(
        self,
        name,
        description,
        total_amount,
        tax_type,
        method_type,
        tactic_category,
    ):
        self.name = name
        self.description = description
        self.total_amount = total_amount
        self.exposed_amount = 0
        self.tax_type = tax_type
        self.method_type = method_type
        self.tactic_category = tactic_category


class Company:
    def __init__(
        self,
        name,
        size,
        description,
        real_case_desc,
        revenue,
        operating_income,
        tax_target,
        team_hp_damage,
        tactics,
        defense_actions,
    ):
        self.name = name
        self.size = size
        self.description = description
        self.real_case_desc = real_case_desc
        self.revenue = revenue  # 억원 단위 (표시는 병기)
        self.operating_income = operating_income  # 억원 단위
        self.tax_target = tax_target  # 백만원 단위
        self.team_hp_damage = team_hp_damage
        self.current_collected_tax = 0
        self.tactics = tactics
        self.defense_actions = defense_actions


class Artifact:
    def __init__(self, name, description, effect):
        self.name = name
        self.description = description
        self.effect = effect


# ---- (C) 게임 DB ------------------------------------------------------
TAX_MAN_DB = {
    "lim": TaxManCard(
        name="임향수",
        grade_num=4,
        position="팀장",
        cost=0,
        hp=150,
        focus=4,
        analysis=10,
        persuasion=10,
        evidence=10,
        data=10,
        description="국세청 최고의 '조사통'.",
        ability_name="[기획 조사]",
        ability_desc="매 턴 집중력 +1. 분석/데이터 카드 피해 +10.",
    ),
    "han": TaxManCard(
        name="한중히",
        grade_num=5,
        position="팀장",
        cost=0,
        hp=100,
        focus=3,
        analysis=9,
        persuasion=6,
        evidence=8,
        data=9,
        description="국제조세 최고 권위자.",
        ability_name="[역외탈세 추적]",
        ability_desc="외국계/자본 거래 피해 +30%.",
    ),
    "baek": TaxManCard(
        name="백용호",
        grade_num=5,
        position="팀장",
        cost=0,
        hp=110,
        focus=3,
        analysis=7,
        persuasion=10,
        evidence=9,
        data=7,
        description="'과학적 세정' 선구자.",
        ability_name="[TIS 분석]",
        ability_desc="데이터 카드 비용 -1.",
    ),
    "seo": TaxManCard(
        name="서영택",
        grade_num=6,
        position="팀장",
        cost=0,
        hp=120,
        focus=3,
        analysis=8,
        persuasion=9,
        evidence=8,
        data=7,
        description="'대기업 저격수' 원조.",
        ability_name="[대기업 저격]",
        ability_desc="대기업/외국계 법인세 카드 피해 +25%.",
    ),
    "kim": TaxManCard(
        name="김철주",
        grade_num=6,
        position="조사반장",
        cost=0,
        hp=130,
        focus=3,
        analysis=6,
        persuasion=8,
        evidence=9,
        data=5,
        description="'지하경제' 양성화 전문가.",
        ability_name="[압수수색]",
        ability_desc="'현장 압수수색' 사용 시 15% 확률로 '결정적 증거' 획득.",
    ),
    "oh": TaxManCard(
        name="전필성",
        grade_num=7,
        position="조사반장",
        cost=0,
        hp=140,
        focus=3,
        analysis=7,
        persuasion=6,
        evidence=7,
        data=8,
        description="TIS 초창기 멤버.",
        ability_name="[데이터 마이닝]",
        ability_desc="적출액 70+ 데이터 카드 피해 +15.",
    ),
    "jo": TaxManCard(
        name="조용규",
        grade_num=7,
        position="조사반장",
        cost=0,
        hp=100,
        focus=4,
        analysis=9,
        persuasion=7,
        evidence=6,
        data=7,
        description="'세금 전도사' 교육원장.",
        ability_name="[세법 교본]",
        ability_desc="'판례 제시', '법령 재검토' 효과 2배.",
    ),
    "park": TaxManCard(
        name="박지연",
        grade_num=8,
        position="일반조사관",
        cost=0,
        hp=90,
        focus=4,
        analysis=7,
        persuasion=5,
        evidence=6,
        data=7,
        description="'세법 신동' 8급 특채.",
        ability_name="[법리 검토]",
        ability_desc="턴 첫 분석/설득 카드 비용 -1.",
    ),
    "lee": TaxManCard(
        name="이철수",
        grade_num=7,
        position="일반조사관",
        cost=0,
        hp=100,
        focus=3,
        analysis=5,
        persuasion=5,
        evidence=5,
        data=5,
        description="열정 넘치는 7급 신입.",
        ability_name="[기본기]",
        ability_desc="'기본 경비 적정성 검토', '단순 경비 처리 오류 지적' 카드 피해 +8.",
    ),
}


LOGIC_CARD_DB = {
    "c_tier_01": LogicCard(
        name="단순 자료 대사",
        cost=0,
        base_damage=5,
        tax_type=["부가세", "법인세"],
        attack_category=["공통"],
        description="매입/매출 자료 단순 비교.",
        text="자료 대사 기본 습득.",
    ),
    "c_tier_02": LogicCard(
        name="법령 재검토",
        cost=0,
        base_damage=0,
        tax_type=["공통"],
        attack_category=["공통"],
        description="카드 1장 뽑기.",
        text="관련 법령 재검토.",
        special_effect={"type": "draw", "value": 1},
    ),
    "util_01": LogicCard(
        name="초과근무",
        cost=1,
        base_damage=0,
        tax_type=["공통"],
        attack_category=["공통"],
        description="카드 2장 뽑기.",
        text="밤샘 근무로 단서 발견!",
        special_effect={"type": "draw", "value": 2},
    ),
    "basic_01": LogicCard(
        name="기본 경비 적정성 검토",
        cost=1,
        base_damage=10,
        tax_type=["법인세"],
        attack_category=["비용"],
        description="기본 비용 처리 적정성 검토.",
        text="법인세법 비용 조항 분석.",
    ),
    "basic_02": LogicCard(
        name="단순 경비 처리 오류 지적",
        cost=1,
        base_damage=12,
        tax_type=["법인세"],
        attack_category=["비용"],
        description="증빙 미비 경비 지적.",
        text="증빙 대조 기본 습득.",
    ),
    "b_tier_04": LogicCard(
        name="세금계산서 대사",
        cost=1,
        base_damage=15,
        tax_type=["부가세"],
        attack_category=["수익", "비용"],
        description="매입/매출 세금계산서 합계표 대조.",
        text="합계표 불일치 확인.",
    ),
    "c_tier_03": LogicCard(
        name="가공 증빙 수취 분석",
        cost=2,
        base_damage=15,
        tax_type=["법인세", "부가세"],
        attack_category=["비용"],
        description="실물 없는 증빙 수취 분석.",
        text="가짜 세금계산서 흐름 파악.",
    ),
    "corp_01": LogicCard(
        name="접대비 한도 초과",
        cost=2,
        base_damage=25,
        tax_type=["법인세"],
        attack_category=["비용"],
        description="법정 한도 초과 접대비 손금불산입.",
        text="법인세법 접대비 조항 습득.",
    ),
    "b_tier_03": LogicCard(
        name="판례 제시",
        cost=2,
        base_damage=22,
        tax_type=["공통"],
        attack_category=["공통"],
        description="유사 오류 판례 제시.",
        text="대법원 판례 제시.",
        special_bonus={"target_method": "단순 오류", "multiplier": 2.0, "bonus_desc": "단순 오류에 2배 피해"},
    ),
    "b_tier_05": LogicCard(
        name="인건비 허위 계상",
        cost=2,
        base_damage=30,
        tax_type=["법인세"],
        attack_category=["비용"],
        description="미근무 친인척 인건비 처리.",
        text="급여대장-근무 내역 불일치 확인.",
    ),
    "util_02": LogicCard(
        name="빅데이터 분석",
        cost=2,
        base_damage=0,
        tax_type=["공통"],
        attack_category=["공통"],
        description="적 혐의 유형과 일치하는 카드 1장 서치.",
        text="TIS 빅데이터 패턴 발견!",
        special_effect={"type": "search_draw", "value": 1},
    ),
    "corp_02": LogicCard(
        name="업무 무관 자산 비용 처리",
        cost=3,
        base_damage=35,
        tax_type=["법인세"],
        attack_category=["비용"],
        description="대표 개인 차량 유지비 등 적발.",
        text="벤츠 운행일지 확보!",
        special_bonus={"target_method": "고의적 누락", "multiplier": 1.5, "bonus_desc": "고의적 누락에 1.5배 피해"},
    ),
    "b_tier_01": LogicCard(
        name="금융거래 분석",
        cost=3,
        base_damage=45,
        tax_type=["법인세"],
        attack_category=["수익", "자본"],
        description="의심 자금 흐름 추적.",
        text="FIU 분석 기법 습득.",
    ),
    "b_tier_02": LogicCard(
        name="현장 압수수색",
        cost=3,
        base_damage=25,
        tax_type=["공통"],
        attack_category=["공통"],
        description="현장 방문, 장부-실물 대조.",
        text="재고 불일치 확인.",
        special_bonus={"target_method": "고의적 누락", "multiplier": 2.0, "bonus_desc": "고의적 누락에 2배 피해"},
    ),
    "a_tier_02": LogicCard(
        name="차명계좌 추적",
        cost=3,
        base_damage=50,
        tax_type=["법인세", "부가세"],
        attack_category=["수익"],
        description="타인 명의 계좌 수입 추적.",
        text="차명계좌 흐름 파악.",
        special_bonus={"target_method": "고의적 누락", "multiplier": 2.0, "bonus_desc": "고의적 누락에 2배 피해"},
    ),
    "a_tier_01": LogicCard(
        name="자금출처조사",
        cost=4,
        base_damage=90,
        tax_type=["법인세"],
        attack_category=["자본"],
        description="고액 자산가 불분명 자금 출처 추적.",
        text="수십 개 차명계좌 흐름 파악.",
    ),
    "s_tier_01": LogicCard(
        name="국제거래 과세논리",
        cost=4,
        base_damage=65,
        tax_type=["법인세"],
        attack_category=["자본"],
        description="TP 조작, 역외탈세 적발.",
        text="BEPS 보고서 이해.",
        special_bonus={"target_method": "자본 거래", "multiplier": 2.0, "bonus_desc": "자본 거래에 2배 피해"},
    ),
    "s_tier_02": LogicCard(
        name="조세피난처 역외탈세",
        cost=5,
        base_damage=130,
        tax_type=["법인세"],
        attack_category=["자본"],
        description="SPC 이용 해외 소득 은닉 적발.",
        text="BVI, 케이맨 SPC 실체 규명.",
        special_bonus={"target_method": "자본 거래", "multiplier": 1.5, "bonus_desc": "자본 거래에 1.5배 피해"},
    ),
}


ARTIFACT_DB = {
    "coffee": Artifact(
        name="☕ 믹스 커피",
        description="턴 시작 시 집중력 +1.",
        effect={"type": "on_turn_start", "value": 1, "subtype": "focus"},
    ),
    "forensic": Artifact(
        name="💻 포렌식 장비",
        description="효과 없음 (명확도 제거됨).",
        effect={"type": "on_battle_start", "value": 0, "subtype": "none"},
    ),
    "vest": Artifact(
        name="🛡️ 방탄 조끼",
        description="전투 시작 시 보호막 +30.",
        effect={"type": "on_battle_start", "value": 30, "subtype": "shield"},
    ),
    "plan": Artifact(
        name="📜 조사계획서",
        description="첫 턴 카드 +1장.",
        effect={"type": "on_battle_start", "value": 1, "subtype": "draw"},
    ),
    "recorder": Artifact(
        name="🎤 녹음기",
        description="효과 없음 (명확도 제거됨).",
        effect={"type": "on_turn_start", "value": 0, "subtype": "none"},
    ),
    "book": Artifact(
        name="📖 오래된 법전",
        description="'판례 제시', '법령 재검토' 비용 -1.",
        effect={"type": "on_cost_calculate", "value": -1, "target_cards": ["판례 제시", "법령 재검토"]},
    ),
}


COMPANY_DB = [
    Company(
        name="(주)가나푸드",
        size="소규모",
        revenue=50,
        operating_income=5,
        tax_target=5,
        team_hp_damage=(5, 10),
        description="중소 유통업체. 사장 SNS는 슈퍼카와 명품 사진 가득.",
        real_case_desc=(
            "[교육] 소규모 법인은 대표가 법인 자금을 개인 돈처럼 쓰는 경우가 빈번합니다. "
            "법인카드로 명품 구매, 개인 차량 유지비 처리 등은 '업무 무관 비용'으로 손금 불인정되고, "
            "대표 상여 처리되어 소득세가 추가 과세될 수 있습니다."
        ),
        tactics=[
            EvasionTactic(
                "사주 개인적 사용",
                "대표가 배우자 명의 외제차 리스료 월 500만원 법인 처리, 주말 골프 비용, 자녀 학원비 등 법인카드로 결제.",
                3,
                tax_type="법인세",
                method_type="고의적 누락",
                tactic_category="비용",
            ),
            EvasionTactic(
                "증빙 미비 경비",
                "실제 거래 없이 서류상 거래처 명절 선물 1천만원 꾸미고, 관련 증빙(세금계산서, 입금표) 제시 못함.",
                2,
                tax_type=["법인세", "부가세"],
                method_type="단순 오류",
                tactic_category="비용",
            ),
        ],
        defense_actions=["담당 세무사가 시간 끌기.", "대표가 '사실무근' 주장.", "경리 직원이 '실수' 변명."],
    ),
    Company(
        name="㈜넥신 (Nexin)",
        size="중견기업",
        revenue=1000,
        operating_income=100,
        tax_target=20,
        team_hp_damage=(10, 25),
        description="급성장 게임/IT 기업. 복잡한 지배구조와 관계사 거래.",
        # [업데이트] SW 과세 안내 최신화
        real_case_desc=(
            "[교육] IT 기업의 과세는 용역 내용에 따라 달라지지만, 2001.7.1. 이후 일반적인 SW 개발·유지보수는 원칙적으로 과세 대상입니다. "
            "특수관계법인에 용역비를 과다 지급하는 경우에는 '부당행위계산부인' 검토가 필요합니다."
        ),
        tactics=[
            EvasionTactic(
                "과면세 오류",
                "과세 대상 'SW 유지보수' 용역 매출 5억원을 면세 'SW 개발'로 위장 신고하여 부가세 누락.",
                8,
                tax_type="부가세",
                method_type="단순 오류",
                tactic_category="수익",
            ),
            EvasionTactic(
                "관계사 부당 지원",
                "대표 아들 소유 페이퍼컴퍼니에 '경영 자문' 명목으로 시가(월 500)보다 높은 월 3천만원 지급.",
                12,
                tax_type="법인세",
                method_type="자본 거래",
                tactic_category="자본",
            ),
        ],
        defense_actions=["회계법인이 '정상 거래' 주장.", "자료가 '서버 오류'로 삭제 주장.", "실무자가 '모른다'며 비협조."],
    ),
    Company(
        name="(주)한늠석유 (자료상)",
        size="중견기업",
        revenue=500,
        operating_income=-10,
        tax_target=30,
        team_hp_damage=(15, 30),
        description="전형적인 '자료상'. 가짜 석유 유통, 허위 세금계산서 발행.",
        real_case_desc=(
            "[교육] '자료상'은 폭탄업체, 중간 유통 등 여러 단계를 거쳐 허위 세금계산서를 유통시킵니다. "
            "부가세 부당 공제, 가공 경비 계상 등으로 세금을 탈루하며 조세범처벌법상 중범죄입니다."
        ),
        tactics=[
            EvasionTactic(
                "허위 세금계산서 발행",
                "실물 없이 폭탄업체로부터 받은 허위 세금계산서(가짜 석유) 수십억 원어치를 최종 소비자에게 발행하여 매입세액 부당 공제.",
                20,
                tax_type="부가세",
                method_type="고의적 누락",
                tactic_category="비용",
            ),
            EvasionTactic(
                "가공 매출 누락",
                "대포통장 등 차명계좌로 매출 대금 수백억원 수령 후, 세금계산서 미발행으로 부가세/법인세 소득 누락.",
                10,
                tax_type=["법인세", "부가세"],
                method_type="고의적 누락",
                tactic_category="수익",
            ),
        ],
        defense_actions=["대표 해외 도피.", "사무실 텅 빔 (페이퍼컴퍼니).", "대포폰/대포통장 외 단서 없음."],
    ),
    Company(
        name="㈜삼숭물산 (Samsoong)",
        size="대기업",
        revenue=50000,
        operating_income=2000,
        tax_target=100,
        team_hp_damage=(20, 40),
        description="대한민국 최고 대기업. 복잡한 순환출자, 경영권 승계 이슈.",
        real_case_desc=(
            "[교육] 대기업 경영권 승계 시 '일감 몰아주기'는 단골 탈루 유형입니다. 총수 일가 보유 비상장 계열사에 이익을 몰아주어 편법 증여합니다. "
            "'불공정 합병'으로 지배력을 강화하며 세금 없는 부의 이전을 꾀하기도 합니다."
        ),
        tactics=[
            EvasionTactic(
                "일감 몰아주기",
                "총수 2세 지분 100% 비상장 'A사'에 그룹 SI 용역을 수의계약으로 고가 발주, 연 수천억원 이익 몰아줌.",
                50,
                tax_type="법인세",
                method_type="자본 거래",
                tactic_category="자본",
            ),
            EvasionTactic(
                "가공 세금계산서 수취",
                "실거래 없는 유령 광고대행사로부터 수백억 원대 가짜 세금계산서 받아 비용 부풀리고 부가세 부당 환급.",
                30,
                tax_type="부가세",
                method_type="고의적 누락",
                tactic_category="비용",
            ),
            EvasionTactic(
                "불공정 합병",
                "총수 일가 유리하도록 계열사 합병 비율 조작, 편법으로 경영권 승계 및 이익 증여.",
                20,
                tax_type="법인세",
                method_type="자본 거래",
                tactic_category="자본",
            ),
        ],
        defense_actions=[
            "최고 로펌 '김&장' 대응팀 꾸림.",
            "로펌 '정상 경영 활동' 의견서 제출.",
            "언론에 '과도한 세무조사' 여론전.",
            "정치권 통해 조사 중단 압력.",
        ],
    ),
    Company(
        name="구갈 코리아(유) (Googal)",
        size="외국계",
        revenue=2000,
        operating_income=300,
        tax_target=80,
        team_hp_damage=(15, 30),
        description="다국적 IT 기업 한국 지사. '이전가격(TP)' 조작 통한 소득 해외 이전 혐의.",
        real_case_desc=(
            "[교육] 다국적 IT 기업은 조세 조약 및 세법 허점을 이용한 공격적 조세회피(ATP) 전략을 사용합니다. "
            "저세율국 자회사에 '경영자문료', '라이선스비' 명목으로 이익을 이전시키는 '이전가격(TP)' 조작이 대표적입니다. "
            "OECD 'BEPS 프로젝트' 등 국제 공조로 대응 중입니다."
        ),
        tactics=[
            EvasionTactic(
                "이전가격(TP) 조작",
                "버뮤다 페이퍼컴퍼니 자회사에 국내 매출 상당 부분을 'IP 사용료' 명목으로 지급하여 국내 이익 축소.",
                50,
                tax_type="법인세",
                method_type="자본 거래",
                tactic_category="자본",
            ),
            EvasionTactic(
                "고정사업장 미신고",
                "국내 서버팜 운영하며 광고 수익 창출함에도 '단순 지원 용역'으로 위장, 고정사업장 신고 회피.",
                30,
                tax_type="법인세",
                method_type="고의적 누락",
                tactic_category="수익",
            ),
        ],
        defense_actions=["미 본사 '영업 비밀' 이유로 자료 제출 거부.", "조세 조약 근거 상호 합의(MAP) 신청 압박.", "자료 영어로만 제출, 번역 지연."],
    ),
    Company(
        name="(주)씨엔해운 (C&)",
        size="대기업",
        revenue=10000,
        operating_income=500,
        tax_target=150,
        team_hp_damage=(25, 45),
        description="'선백왕' 운영 해운사. 조세피난처 페이퍼컴퍼니 이용 탈루 혐의.",
        real_case_desc=(
            "[교육] 선박 등 고가 자산 산업은 조세피난처(Tax Haven) SPC를 이용한 역외탈세가 빈번합니다. "
            "BVI 등에 페이퍼컴퍼니를 세우고 리스료 수입 등을 빼돌려 국내 세금을 회피합니다. 국제거래조사국의 주요 대상입니다."
        ),
        tactics=[
            EvasionTactic(
                "역외탈세 (SPC)",
                "파나마, BVI 등 페이퍼컴퍼니(SPC) 명의로 선박 운용, 국내 리스료 수입 수천억원 은닉.",
                100,
                tax_type="법인세",
                method_type="자본 거래",
                tactic_category="수익",
            ),
            EvasionTactic(
                "선박 취득가액 조작",
                "노후 선박 해외 SPC에 저가 양도 후, SPC가 고가로 제3자 매각, 양도 차익 수백억원 은닉.",
                50,
                tax_type="법인세",
                method_type="고의적 누락",
                tactic_category="자본",
            ),
        ],
        defense_actions=["해외 법인 대표 연락 두절.", "이면 계약서 존재 첩보.", "국내 법무팀 '해외 법률 검토 필요' 대응 지연."],
    ),
]


# ---- (D) 게임 상태 관리 ---------------------------------------------

def initialize_game():
    # (선택) 난수 시드
    seed = st.session_state.get("seed", None)
    if seed is not None:
        try:
            random.seed(int(seed))
        except Exception:
            pass

    team_members = []
    lead_candidates = [m for m in TAX_MAN_DB.values() if m.grade_num <= 6 and "팀장" in m.position]
    team_members.append(random.choice(lead_candidates))

    chief_candidates = [m for m in TAX_MAN_DB.values() if 6 <= m.grade_num <= 7 and "반장" in m.position]
    num_chiefs = random.randint(1, 2)
    team_members.extend(random.sample(chief_candidates, min(num_chiefs, len(chief_candidates))))

    officer_candidates = [m for m in TAX_MAN_DB.values() if 7 <= m.grade_num <= 8 and "조사관" in m.position]
    num_officers = 5 - len(team_members)
    team_members.extend(random.sample(officer_candidates, min(num_officers, len(officer_candidates))))

    st.session_state.player_team = team_members

    start_deck = (
        [LOGIC_CARD_DB["basic_01"]] * 4
        + [LOGIC_CARD_DB["basic_02"]] * 3
        + [LOGIC_CARD_DB["b_tier_04"]] * 3
        + [LOGIC_CARD_DB["c_tier_03"]] * 2
        + [LOGIC_CARD_DB["c_tier_02"]] * 2
    )
    st.session_state.player_deck = random.sample(start_deck, len(start_deck))
    st.session_state.player_hand = []
    st.session_state.player_discard = []

    start_artifact_keys = ["coffee", "vest", "plan", "book"]
    random_artifact_key = random.choice(start_artifact_keys)
    st.session_state.player_artifacts = [ARTIFACT_DB[random_artifact_key]]

    st.session_state.team_max_hp = sum(member.hp for member in team_members)
    st.session_state.team_hp = st.session_state.team_max_hp
    st.session_state.team_shield = 0

    st.session_state.player_focus_max = sum(member.focus for member in team_members)
    st.session_state.player_focus_current = st.session_state.player_focus_max

    st.session_state.current_battle_company = None
    st.session_state.battle_log = []
    st.session_state.selected_card_index = None
    st.session_state.bonus_draw = 0

    st.session_state.company_order = random.sample(COMPANY_DB, len(COMPANY_DB))

    st.session_state.game_state = "MAP"
    st.session_state.current_stage_level = 0
    st.session_state.total_collected_tax = 0


# ---- (E) 턴/행동 로직 -------------------------------------------------

def start_player_turn():
    base_focus = sum(member.focus for member in st.session_state.player_team)
    st.session_state.player_focus_current = base_focus

    if "임향수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current += 1
        log_message("✨ [기획 조사] 효과로 집중력 +1!", "info")

    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_turn_start" and artifact.effect["subtype"] == "focus":
            st.session_state.player_focus_current += artifact.effect["value"]
            log_message(f"✨ {artifact.name} 효과로 집중력 +{artifact.effect['value']}!", "info")

    st.session_state.player_focus_max = st.session_state.player_focus_current

    cards_to_draw = 4 + st.session_state.get("bonus_draw", 0)
    if st.session_state.get("bonus_draw", 0) > 0:
        log_message(
            f"✨ {ARTIFACT_DB['plan'].name} 효과로 카드 {st.session_state.bonus_draw}장 추가 드로우!",
            "info",
        )
        st.session_state.bonus_draw = 0

    draw_cards(cards_to_draw)
    check_draw_cards_in_hand()
    log_message("--- 플레이어 턴 시작 ---")
    st.session_state.turn_first_card_played = True
    st.session_state.selected_card_index = None


def draw_cards(num_to_draw):
    drawn_cards = []
    for _ in range(num_to_draw):
        if not st.session_state.player_deck:
            if not st.session_state.player_discard:
                log_message("경고: 더 이상 뽑을 카드가 없습니다!", "error")
                break
            log_message("덱이 비어, 버린 카드를 섞습니다.")
            st.session_state.player_deck = random.sample(
                st.session_state.player_discard, len(st.session_state.player_discard)
            )
            st.session_state.player_discard = []
            if not st.session_state.player_deck:
                log_message("경고: 덱과 버린 덱이 모두 비었습니다!", "error")
                break
        if not st.session_state.player_deck:
            log_message("경고: 카드를 뽑으려 했으나 덱이 비었습니다!", "error")
            break
        card = st.session_state.player_deck.pop()
        drawn_cards.append(card)
    st.session_state.player_hand.extend(drawn_cards)


def check_draw_cards_in_hand():
    cards_to_play_indices = []
    for i, card in enumerate(st.session_state.player_hand):
        if card.cost == 0 and card.special_effect and card.special_effect.get("type") == "draw":
            cards_to_play_indices.append(i)

    cards_to_play_indices.reverse()
    total_draw_value = 0
    for index in cards_to_play_indices:
        if index < len(st.session_state.player_hand):
            card_to_play = st.session_state.player_hand.pop(index)
            st.session_state.player_discard.append(card_to_play)
            log_message(
                f"✨ [{card_to_play.name}] 효과 발동! 카드 {card_to_play.special_effect.get('value', 0)}장을 뽑습니다.",
                "info",
            )
            draw_value = card_to_play.special_effect.get("value", 0)
            if "조용규" in [m.name for m in st.session_state.player_team] and card_to_play.name == "법령 재검토":
                log_message("✨ [세법 교본] 효과로 카드 1장 추가 드로우!", "info")
                draw_value *= 2
            total_draw_value += draw_value
        else:
            log_message(f"경고: 드로우 카드 처리 중 인덱스 오류 발생 (index: {index})", "error")

    if total_draw_value > 0:
        draw_cards(total_draw_value)


def select_card_to_play(card_index):
    if "player_hand" not in st.session_state or card_index >= len(st.session_state.player_hand):
        st.toast("오류: 유효하지 않은 카드입니다.", icon="🚨")
        return

    card = st.session_state.player_hand[card_index]
    cost_to_pay = calculate_card_cost(card)

    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠")
        return

    if card.special_effect and card.special_effect.get("type") == "search_draw":
        execute_search_draw(card_index)
        st.rerun()
    else:
        st.session_state.selected_card_index = card_index
        st.rerun()


def execute_search_draw(card_index):
    if card_index is None or card_index >= len(st.session_state.player_hand):
        return
    card = st.session_state.player_hand[card_index]
    cost_to_pay = calculate_card_cost(card)
    if st.session_state.player_focus_current < cost_to_pay:
        return

    st.session_state.player_focus_current -= cost_to_pay
    st.session_state.turn_first_card_played = False

    enemy_tactic_categories = list(
        set(
            [
                t.tactic_category
                for t in st.session_state.current_battle_company.tactics
                if t.exposed_amount < t.total_amount
            ]
        )
    )
    if not enemy_tactic_categories:
        log_message("ℹ️ [빅데이터 분석] 분석할 적 혐의가 남아있지 않습니다.", "info")
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
        return

    search_pool = st.session_state.player_deck + st.session_state.player_discard
    random.shuffle(search_pool)

    found_card = None
    for pool_card in search_pool:
        if pool_card.cost > 0 and "공통" not in pool_card.attack_category:
            if any(cat in enemy_tactic_categories for cat in pool_card.attack_category):
                found_card = pool_card
                break
    if found_card:
        log_message(
            f"📊 [빅데이터 분석] 적 혐의({', '.join(enemy_tactic_categories)})와 관련된 '{found_card.name}' 카드를 찾았습니다!",
            "success",
        )
        st.session_state.player_hand.append(found_card)
        try:
            st.session_state.player_deck.remove(found_card)
        except ValueError:
            try:
                st.session_state.player_discard.remove(found_card)
            except ValueError:
                log_message("경고: 빅데이터 분석 카드 제거 중 오류 발생", "error")
    else:
        log_message("ℹ️ [빅데이터 분석] 관련 카드를 찾지 못했습니다...", "info")

    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
    check_draw_cards_in_hand()


def cancel_card_selection():
    st.session_state.selected_card_index = None
    st.rerun()


def calculate_card_cost(card):
    cost_to_pay = card.cost

    if "백용호" in [m.name for m in st.session_state.player_team] and (
        ("데이터" in card.name) or ("분석" in card.name)
    ):
        cost_to_pay = max(0, cost_to_pay - 1)

    card_type_match = ("분석" in card.name) or ("판례" in card.name) or ("법령" in card.name)
    if (
        "박지연" in [m.name for m in st.session_state.player_team]
        and st.session_state.get("turn_first_card_played", True)
        and card_type_match
    ):
        cost_to_pay = max(0, cost_to_pay - 1)

    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_cost_calculate":
            if card.name in artifact.effect.get("target_cards", []):
                cost_to_pay = max(0, cost_to_pay + artifact.effect["value"])

    return cost_to_pay


def execute_attack(card_index, tactic_index):
    if (
        card_index is None
        or card_index >= len(st.session_state.player_hand)
        or tactic_index >= len(st.session_state.current_battle_company.tactics)
    ):
        st.toast("오류: 공격 실행 중 오류가 발생했습니다.", icon="🚨")
        st.session_state.selected_card_index = None
        st.rerun()
        return

    card = st.session_state.player_hand[card_index]
    tactic = st.session_state.current_battle_company.tactics[tactic_index]
    company = st.session_state.current_battle_company

    # 일치 여부
    is_tax_match = ("공통" in card.tax_type) or (
        isinstance(tactic.tax_type, list) and any(tt in card.tax_type for tt in tactic.tax_type)
    ) or (tactic.tax_type in card.tax_type)
    is_category_match = ("공통" in card.attack_category) or (tactic.tactic_category in card.attack_category)

    # 안전 모드: 불일치 공격 차단
    if st.session_state.get("safe_mode", SAFE_MODE_DEFAULT):
        if not is_tax_match or not is_category_match:
            st.toast("안전 모드: 세목/유형 불일치 공격은 차단됩니다.", icon="🛡️")
            return

    if not is_tax_match:
        log_message(
            f"❌ [세목 불일치!] '{card.name}'(은)는 '{tactic.tax_type}' 혐의에 부적절합니다! (팀 체력 -10)",
            "error",
        )
        st.session_state.team_hp -= 10
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
        st.session_state.selected_card_index = None
        check_battle_end()
        st.rerun()
        return

    if not is_category_match:
        log_message(
            f"🚨 [유형 불일치!] '{card.name}'(은)는 '{tactic.tactic_category}' 혐의({tactic.name})에 맞지 않는 조사 방식입니다! (팀 체력 -5)",
            "error",
        )
        st.session_state.team_hp -= 5
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
        st.session_state.selected_card_index = None
        check_battle_end()
        st.rerun()
        return

    cost_to_pay = calculate_card_cost(card)
    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠")
        st.session_state.selected_card_index = None
        st.rerun()
        return

    st.session_state.player_focus_current -= cost_to_pay
    if st.session_state.get("turn_first_card_played", True):
        st.session_state.turn_first_card_played = False

    damage = card.base_damage

    # [버그 픽스] 이철수 시너지: 실제 카드명에 맞게 체크
    if (
        "이철수" in [m.name for m in st.session_state.player_team]
        and card.name in ["기본 경비 적정성 검토", "단순 경비 처리 오류 지적"]
    ):
        damage += 8
        log_message("✨ [기본기] +8!", "info")

    if "임향수" in [m.name for m in st.session_state.player_team] and (
        ("분석" in card.name) or ("자료" in card.name) or ("추적" in card.name)
    ):
        damage += 10
        log_message("✨ [기획 조사] +10!", "info")

    bonus_multiplier = 1.0
    if card.special_bonus and card.special_bonus.get("target_method") == tactic.method_type:
        bonus_multiplier = card.special_bonus.get("multiplier", 1.0)
        if "조용규" in [m.name for m in st.session_state.player_team] and card.name == "판례 제시":
            bonus_multiplier *= 2
            log_message("✨ [세법 교본] '판례 제시' 2배!", "info")
        else:
            log_message(
                f"🔥 [정확한 지적!] '{card.name}' perfectly matches '{tactic.method_type}'!",
                "warning",
            )

    if "한중히" in [m.name for m in st.session_state.player_team] and (
        company.size == "외국계" or tactic.method_type == "자본 거래"
    ):
        bonus_multiplier *= 1.3
        log_message("✨ [역외탈세 추적] +30%!", "info")

    if "서영택" in [m.name for m in st.session_state.player_team] and (
        company.size in ["대기업", "외국계"] and ("법인세" in card.tax_type)
    ):
        bonus_multiplier *= 1.25
        log_message("✨ [대기업 저격] +25%!", "info")

    final_damage = int(damage * bonus_multiplier)
    tactic.exposed_amount += final_damage
    company.current_collected_tax += final_damage

    if bonus_multiplier >= 2.0:
        log_message(f"💥 [치명타!] '{card.name}' hits for **{fmt_baekman(final_damage)}**!", "success")
    elif bonus_multiplier > 1.0:
        log_message(f"👍 [효과적!] '{card.name}' hits for **{fmt_baekman(final_damage)}**.", "success")
    else:
        log_message(f"▶️ [적중] '{card.name}' hits for **{fmt_baekman(final_damage)}**.", "success")

    if tactic.exposed_amount >= tactic.total_amount and not getattr(tactic, "is_cleared", False):
        tactic.is_cleared = True
        log_message(
            f"🔥 [{tactic.name}] fully exposed ({fmt_baekman(tactic.total_amount)})!",
            "warning",
        )
        if "벤츠" in card.text:
            log_message("💬 [현장] 법인소유 벤츠 발견!", "info")
        if "압수수색" in card.name:
            log_message("💬 [현장] 비밀장부 확보!", "info")

    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
    st.session_state.selected_card_index = None
    check_battle_end()
    st.rerun()


def end_player_turn():
    st.session_state.player_discard.extend(st.session_state.player_hand)
    st.session_state.player_hand = []
    st.session_state.selected_card_index = None

    log_message("--- 기업 턴 시작 ---")
    enemy_turn()

    if not check_battle_end():
        start_player_turn()
        st.rerun()


def enemy_turn():
    company = st.session_state.current_battle_company
    action_desc = random.choice(company.defense_actions)
    min_dmg, max_dmg = company.team_hp_damage
    damage = random.randint(min_dmg, max_dmg)

    damage_to_shield = min(st.session_state.get("team_shield", 0), damage)
    damage_to_hp = damage - damage_to_shield
    st.session_state.team_shield -= damage_to_shield
    st.session_state.team_hp -= damage_to_hp

    log_prefix = "◀️ [기업]"
    if company.size in ["대기업", "외국계"] and "로펌" in action_desc:
        log_prefix = "◀️ [로펌]"

    if damage_to_shield > 0:
        log_message(
            f"{log_prefix} {action_desc} (🛡️-{damage_to_shield}, ❤️-{damage_to_hp}!)",
            "error",
        )
    else:
        log_message(f"{log_prefix} {action_desc} (팀 사기 저하 ❤️-{damage}!)", "error")


def check_battle_end():
    company = st.session_state.current_battle_company

    if company.current_collected_tax >= company.tax_target:
        bonus = company.current_collected_tax - company.tax_target
        log_message(
            f"🎉 [조사 승리] 목표 {fmt_baekman(company.tax_target)} 달성!",
            "success",
        )
        log_message(f"💰 초과 추징 {fmt_baekman(bonus)} 획득!", "success")
        st.session_state.total_collected_tax += company.current_collected_tax
        st.session_state.game_state = "REWARD"
        if st.session_state.player_discard:
            last_card_text = st.session_state.player_discard[-1].text
            st.toast(f"승리! \"{last_card_text}\"", icon="🎉")
        return True

    if st.session_state.team_hp <= 0:
        st.session_state.team_hp = 0
        log_message("‼️ [조사 중단] 팀 체력 소진...", "error")
        st.session_state.game_state = "GAME_OVER"
        return True
    return False


def start_battle(company_template):
    company = copy.deepcopy(company_template)
    st.session_state.current_battle_company = company
    st.session_state.game_state = "BATTLE"
    st.session_state.battle_log = [f"--- {company.name} ({company.size}) 조사 시작 ---"]

    if st.session_state.player_artifacts:
        start_artifact = st.session_state.player_artifacts[0]
        log_message(f"✨ [조사도구] '{start_artifact.name}' 효과 준비.", "info")

    st.session_state.team_shield = 0
    st.session_state.bonus_draw = 0

    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_battle_start":
            if artifact.effect["subtype"] == "shield":
                shield_gain = artifact.effect["value"]
                st.session_state.team_shield += shield_gain
                log_message(f"✨ {artifact.name} 보호막 +{shield_gain}!", "info")
            elif artifact.effect["subtype"] == "draw":
                st.session_state.bonus_draw += artifact.effect["value"]

    st.session_state.player_deck.extend(st.session_state.player_discard)
    st.session_state.player_deck = random.sample(
        st.session_state.player_deck, len(st.session_state.player_deck)
    )
    st.session_state.player_discard = []
    st.session_state.player_hand = []

    start_player_turn()


def log_message(message, level="normal"):
    color = COLOR.get(level, "")
    if level != "normal":
        message = f":{color}[{message}]"
    st.session_state.battle_log.insert(0, message)
    if len(st.session_state.battle_log) > 30:
        st.session_state.battle_log.pop()


# ---- (F) UI ------------------------------------------------------------

def show_main_menu():
    st.title("💼 세무조사: 덱빌딩 로그라이크")
    st.markdown("---")
    st.header("국세청에 오신 것을 환영합니다.")
    st.write(
        "당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오."
    )
    st.image(
        "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?ixlib=rb-4.0.3&q=80&w=1080",
        caption="국세청 조사국의 풍경 (상상도)",
        use_container_width=True,
    )

    if st.button("🚨 조사 시작 (신규 게임)", type="primary", use_container_width=True):
        initialize_game()
        st.rerun()

    with st.expander("📖 게임 방법 (필독!)", expanded=True):
        st.markdown(
            """
        **1. 🎯 게임 목표**
        - 무작위 팀으로 기업들을 조사하여 **'목표 추징 세액'** 을 달성하면 승리.

        **2. ⚔️ 전투 방식**
        - ❤️ **팀 체력:** 0 되면 패배. / 🛡️ **보호막:** 체력 대신 소모. / 🧠 **집중력:** 카드 사용 자원. / 🃏 **과세논리 카드:** 공격 수단 (턴마다 4장).

        **3. ⚠️ 패널티 시스템**
        - **1. 세목 불일치:** `법인세` 카드로 `부가세` 혐의 공격 시 실패, **팀 체력 -10**. (`공통` 태그 OK)
        - **2. 유형 불일치:** `비용` 카드로 `수익` 혐의 공격 시 실패, **팀 체력 -5**. (`공통` 태그 OK)

        **4. ✨ 유형 보너스**
        - 혐의에는 `고의적 누락`, `단순 오류` 등 **'탈루 유형'** 이 있음.
        - `현장 압수수색`은 '고의적 누락'에 2배 피해, `판례 제시`는 '단순 오류'에 2배 피해. 상황 맞는 카드 사용이 중요!
        """
        )


def show_map_screen():
    st.header(f"📍 조사 지역 (Stage {st.session_state.current_stage_level + 1})")
    st.write("조사할 기업 선택:")

    company_list = st.session_state.company_order
    if st.session_state.current_stage_level < len(company_list):
        company = company_list[st.session_state.current_stage_level]
        with st.container(border=True):
            st.subheader(f"🏢 {company.name} ({company.size})")
            st.write(company.description)

            col1, col2 = st.columns(2)
            col1.metric("매출액", both_units_eok_display(company.revenue))
            col2.metric("영업이익", both_units_eok_display(company.operating_income))

            st.warning(
                f"**예상 턴당 데미지:** {company.team_hp_damage[0]}~{company.team_hp_damage[1]} ❤️"
            )
            st.info(f"**목표 추징 세액:** {fmt_baekman(company.tax_target)} 💰")

            with st.expander("Click: 혐의 및 실제 사례 정보"):
                st.info(f"**[교육 정보]**\n{company.real_case_desc}")
                st.markdown("---")
                st.markdown("**주요 탈루 혐의**")
                for tactic in company.tactics:
                    st.markdown(
                        f"- **{tactic.name}** (`{tactic.tax_type}`, `{tactic.method_type}`, `{tactic.tactic_category}`)"
                    )

            if st.button(
                f"🚨 {company.name} 조사 시작", type="primary", use_container_width=True
            ):
                start_battle(company)
                st.rerun()
    else:
        st.success("🎉 모든 기업 조사 완료! (데모 종료)")
        st.balloons()
        if st.button("🏆 다시 시작"):
            st.session_state.game_state = "MAIN_MENU"
            st.rerun()


def show_battle_screen():
    if not st.session_state.current_battle_company:
        st.error("오류: 기업 정보 없음.")
        st.session_state.game_state = "MAP"
        st.rerun()
        return

    company = st.session_state.current_battle_company

    st.title(f"⚔️ {company.name} 조사 중...")
    st.markdown("---")

    col_left, col_mid, col_right = st.columns([1.2, 1.5, 1.8])

    with col_left:
        st.subheader("👨‍💼 우리 팀")
        st.metric("❤️ 팀 체력", f"{st.session_state.team_hp}/{st.session_state.team_max_hp}")
        st.metric("🛡️ 팀 보호막", f"{st.session_state.get('team_shield', 0)}")
        st.metric(
            "🧠 현재 집중력",
            f"{st.session_state.player_focus_current}/{st.session_state.player_focus_max}",
        )
        st.markdown("---")
        for member in st.session_state.player_team:
            with st.expander(f"**{member.name}** ({member.position}/{member.grade}급)"):
                st.write(f"HP:{member.hp}/{member.max_hp}, Focus:{member.focus}")
                st.info(f"**{member.ability_name}**: {member.ability_desc}")
                st.caption(f"({member.description})")
        st.markdown("---")
        st.subheader("🧰 조사도구")
        if not st.session_state.player_artifacts:
            st.write("(없음)")
        else:
            for artifact in st.session_state.player_artifacts:
                st.success(f"**{artifact.name}**: {artifact.description}")

    with col_mid:
        st.subheader(f"🏢 {company.name} ({company.size})")
        st.progress(
            min(1.0, company.current_collected_tax / company.tax_target),
            text=f"💰 목표 세액: {company.current_collected_tax:,}/{company.tax_target:,} (백만원)",
        )
        st.markdown("---")
        st.subheader("🧾 탈루 혐의 목록")

        is_card_selected = st.session_state.get("selected_card_index") is not None
        if is_card_selected:
            selected_card = st.session_state.player_hand[st.session_state.selected_card_index]
            st.info(f"**'{selected_card.name}'** 카드로 공격할 혐의 선택:")

        if not company.tactics:
            st.write("(모든 혐의 적발!)")

        for i, tactic in enumerate(company.tactics):
            tactic_cleared = tactic.exposed_amount >= tactic.total_amount
            with st.container(border=True):
                st.markdown(
                    f"**{tactic.name}** (`{tactic.tax_type}`/`{tactic.method_type}`/`{tactic.tactic_category}`)"
                )
                st.caption(f"_{tactic.description}_")

                if tactic_cleared:
                    st.progress(
                        1.0,
                        text=f"✅ 적발 완료: {tactic.exposed_amount:,}/{tactic.total_amount:,} (백만원)",
                    )
                else:
                    st.progress(
                        min(1.0, tactic.exposed_amount / tactic.total_amount),
                        text=f"적발액: {tactic.exposed_amount:,}/{tactic.total_amount:,} (백만원)",
                    )

                if is_card_selected and not tactic_cleared:
                    selected_card = st.session_state.player_hand[
                        st.session_state.selected_card_index
                    ]
                    is_tax_match = ("공통" in selected_card.tax_type) or (
                        isinstance(tactic.tax_type, list)
                        and any(tt in selected_card.tax_type for tt in tactic.tax_type)
                    ) or (tactic.tax_type in selected_card.tax_type)
                    is_category_match = ("공통" in selected_card.attack_category) or (
                        tactic.tactic_category in selected_card.attack_category
                    )

                    button_label, button_type = f"🎯 **{tactic.name}** 공격", "primary"
                    if not is_tax_match:
                        button_label, button_type = f"⚠️ (세목 불일치!) {tactic.name}", "secondary"
                    elif not is_category_match:
                        button_label, button_type = f"⚠️ (유형 불일치!) {tactic.name}", "secondary"

                    # [신규] 안전 모드/포커스 부족시 비활성 + 이유 툴팁
                    cost_to_pay = calculate_card_cost(selected_card)
