import streamlit as st
import random
import copy # 기업 객체 복사를 위해 추가

# --- 1. 기본 데이터 구조 정의 ---
# (이전과 동일)
class Card:
    def __init__(self, name, description, cost):
        self.name = name
        self.description = description
        self.cost = cost 

class TaxManCard(Card):
    def __init__(self, name, grade, position, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost)
        self.grade = grade 
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

class LogicCard(Card):
    def __init__(self, name, description, cost, base_damage, tax_type, text, special_effect=None, special_bonus=None):
        super().__init__(name, description, cost)
        self.base_damage = base_damage 
        self.tax_type = tax_type 
        self.text = text 
        self.special_effect = special_effect 
        self.special_bonus = special_bonus 

class EvasionTactic:
    def __init__(self, name, description, total_amount, clarity, tax_type, method_type):
        self.name = name
        self.description = description
        self.total_amount = total_amount 
        self.exposed_amount = 0 
        self.clarity = clarity 
        self.tax_type = tax_type 
        self.method_type = method_type 

class Company:
    def __init__(self, name, size, description, real_case_desc, tax_target, team_hp_damage, tactics, defense_actions):
        self.name = name
        self.size = size 
        self.description = description
        self.real_case_desc = real_case_desc 
        self.tax_target = tax_target 
        self.team_hp_damage = team_hp_damage 
        self.current_collected_tax = 0 
        self.tactics = tactics 
        self.defense_actions = defense_actions 

class Artifact:
    def __init__(self, name, description, effect):
        self.name = name
        self.description = description
        self.effect = effect 

# --- 2. 게임 데이터베이스 (DB) ---

# [조사관 DB] (전원 이름 및 설명 수정)
TAX_MAN_DB = {
    "lim": TaxManCard(
        name="임항수", grade="S", position="팀장", cost=0, hp=150, focus=4, analysis=10, persuasion=10, evidence=10, data=10,
        description="국세청 최고의 '조사통'으로 불렸던 전설. 치밀한 기획력과 저돌적인 돌파력으로 수많은 대기업·대재산가 조사를 성공으로 이끌었다.",
        ability_name="[기획 조사]", ability_desc="매 턴 '집중력'을 1 추가로 얻습니다. '분석력'과 '데이터수집' 기반 카드의 기본 적출액 +5."
    ),
    "han": TaxManCard(
        name="한중희", grade="A", position="팀장", cost=0, hp=100, focus=3, analysis=9, persuasion=6, evidence=8, data=9,
        description="국제조세 분야의 최고 권위자. 조사국장 시절 역외탈세 추적에 큰 공을 세웠으며, '저승사자'라는 별명으로 불렸다.",
        ability_name="[역외탈세 추적]", ability_desc="'외국계' 기업 및 '자본 거래' 유형의 혐의에 주는 모든 피해 +30%."
    ),
    "baek": TaxManCard(
        name="백용후", grade="A", position="팀장", cost=0, hp=110, focus=3, analysis=7, persuasion=10, evidence=9, data=7,
        description="데이터 기반의 '과학적 세정'을 도입한 선구자. 방대한 TIS(국세행정시스템) 데이터를 분석하여 탈루 혐의를 포착하는 데 천재적이다.",
        ability_name="[TIS 분석]", ability_desc="'데이터수집' 기반 카드의 비용이 1 감소하고 (최소 0), '명확도'를 10% 추가로 높입니다."
    ),
    "seo": TaxManCard(
        name="서영태", grade="A", position="팀장", cost=0, hp=120, focus=3, analysis=8, persuasion=9, evidence=8, data=7,
        description="강력한 카리스마와 추진력으로 유명했던 전직 청장. '저승사자'라는 별명이 원조격으로, 특히 대기업 조세포탈에 타협이 없었다.",
        ability_name="[대기업 저격]", ability_desc="'대기업' 또는 '외국계' 기업을 상대로 모든 '법인세' 카드의 최종 적출액 +20%."
    ),
    "kim": TaxManCard(
        name="김철중", grade="B", position="조사반장", cost=0, hp=120, focus=3, analysis=6, persuasion=8, evidence=9, data=5,
        description="'지하경제' 양성화에 앞장 선 현장 전문가. 끈질긴 추적과 동물적인 현장 감각으로 숨겨진 증거를 찾아내는 데 탁월하다.",
        ability_name="[압수수색]", ability_desc="'현장 압수수색' 카드 사용 시 15% 확률로 '결정적 증거(비밀장부)' 카드를 손에 넣는다.(미구현)"
    ),
    "oh": TaxManCard( # (수정)
        name="전필승", grade="B", position="조사반장", cost=0, hp=140, focus=3, analysis=7, persuasion=6, evidence=7, data=8,
        description="국세청 TIS(전산) 시스템 초창기 멤버. '데이터 세정'의 숨은 공로자로, 방대한 전산 자료 속에서 바늘 같은 탈루 혐의를 찾아낸다.",
        ability_name="[데이터 마이닝]", ability_desc="적출액 50 이상인 '데이터수집' 기반 카드의 기본 적출액 +10."
    ),
    "jo": TaxManCard(
        name="조용균", grade="B", position="조사반장", cost=0, hp=100, focus=4, analysis=9, persuasion=7, evidence=6, data=7,
        description="전설적인 세무공무원교육원장 출신. 해박한 세법 지식과 후학 양성으로 '세금 전도사'로 불렸다. 그의 법리 분석은 한 치의 오차도 없다.",
        ability_name="[세법 교본]", ability_desc="'판례 제시' 및 '법령 재검토' 카드의 효과를 2배로 발동시킨다."
    ),
    "park": TaxManCard( # (수정)
        name="박지현", grade="C", position="일반조사관", cost=0, hp=80, focus=4, analysis=7, persuasion=5, evidence=6, data=7,
        description="세무대학을 수석으로 졸업하고 8급으로 임용된 '세법 신동'. 방대한 예규와 판례를 모두 외우고 있어 '걸어다니는 법전'으로 불린다.",
        ability_name="[법리 검토]", ability_desc="매 턴 처음 사용하는 '분석력' 또는 '설득력' 기반 카드의 '집중력' 소모 1 감소."
    ),
    "lee": TaxManCard( # (수정)
        name="이철우", grade="C", position="일반조사관", cost=0, hp=90, focus=3, analysis=5, persuasion=5, evidence=5, data=5,
        description="이제 막 7급 공채로 발령받은 신입 조사관. 열정은 넘치지만 아직 모든 것이 서툴다. 하지만 기본기는 탄탄하여 선배들의 사랑을 받는다.",
        ability_name="[기본기]", ability_desc="'기본 비용 분석'과 '단순 경비 처리 오류 지적' 카드의 기본 적출액 +5."
    )
}

# [과세논리 카드 DB] (변경 없음)
LOGIC_CARD_DB = {
    "c_tier_01": LogicCard(
        name="단순 자료 대사", description="매입/매출 자료를 단순 비교하여 불일치 내역을 찾아냅니다.",
        cost=0, base_damage=3, tax_type=['부가세', '법인세'],
        text="자료 대사의 기본을 익혔다."
    ),
    "c_tier_02": LogicCard(
        name="법령 재검토", description="덱에서 카드 1장을 뽑습니다.",
        cost=0, base_damage=0, tax_type=['공통'],
        text="관련 법령을 다시 한번 검토했다.",
        special_effect={"type": "draw", "value": 1}
    ),
    "c_tier_03": LogicCard(
        name="가공 증빙 수취", description="실물 거래 없이 세금계산서나 영수증을 받아 비용을 부풀립니다. (범용)",
        cost=1, base_damage=8, tax_type=['법인세', '부가세'],
        text="가짜 세금계산서의 흐름을 파악했다."
    ),
    "basic_01": LogicCard(
        name="기본 비용 분석", description="가장 기본적인 세법을 적용하여 비용 누락분을 찾아냅니다.",
        cost=1, base_damage=5, tax_type=['법인세'],
        text="법인세법 기본 비용 조항을 분석했다."
    ),
    "basic_02": LogicCard(
        name="단순 경비 처리 오류 지적", description="증빙이 미비한 간단한 경비 처리를 지적합니다.",
        cost=1, base_damage=6, tax_type=['법인세'],
        text="증빙자료 대조의 기본을 익혔다."
    ),
    "b_tier_04": LogicCard(
        name="세금계산서 대사", description="매입/매출 세금계산서 합계표를 대조하여 불일치 내역을 적발합니다.",
        cost=1, base_damage=10, tax_type=['부가세'],
        text="세금계산서 합계표의 불일치를 확인했다."
    ),
    "corp_01": LogicCard(
        name="접대비 한도 초과", description="법정 한도를 초과한 접대비를 손금불산입합니다.",
        cost=2, base_damage=15, tax_type=['법인세'],
        text="법인세법 18조(접대비)를 습득했다."
    ),
    "corp_02": LogicCard(
        name="업무 무관 자산 비용 처리", description="대표이사의 개인 차량 유지비 등 업무와 무관한 비용을 적발합니다.",
        cost=2, base_damage=20, tax_type=['법인세'],
        text="법인소유 벤츠 S클래스 차량의 운행일지를 확보했다!",
        special_bonus={'target_method': '고의적 누락', 'multiplier': 1.5, 'bonus_desc': '고의적 누락에 1.5배 피해'}
    ),
    "b_tier_01": LogicCard(
        name="금융거래 분석", description="의심스러운 자금 흐름을 포착하여 차명계좌를 추적합니다.",
        cost=2, base_damage=30, tax_type=['법인세'],
        text="FIU 금융정보 분석 기법을 습득했다."
    ),
    "b_tier_02": LogicCard(
        name="현장 압수수색", description="조사 현장에 직접 방문하여 장부와 실물을 대조합니다. '고의적 누락' 혐의에 2배의 피해를 줍니다.",
        cost=2, base_damage=15, tax_type=['공통'],
        text="재고 자산이 장부와 일치하지 않음을 확인했다.",
        special_bonus={'target_method': '고의적 누락', 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}
    ),
    "b_tier_03": LogicCard(
        name="판례 제시", description="유사한 '단순 오류' 혐의에 대한 과거 판례를 제시합니다. '단순 오류' 혐의에 2배의 피해를 줍니다.",
        cost=2, base_damage=15, tax_type=['공통'],
        text="유사 사건의 대법원 판례를 제시했다.",
        special_bonus={'target_method': '단순 오류', 'multiplier': 2.0, 'bonus_desc': '단순 오류에 2배 피해'}
    ),
    "b_tier_05": LogicCard(
        name="인건비 허위 계상", description="근무하지 않는 친인척을 직원으로 올려 인건비를 부당하게 처리합니다.",
        cost=2, base_damage=20, tax_type=['법인세'],
        text="급여대장과 실제 근무 내역의 불일치를 확인했다."
    ),
    "a_tier_02": LogicCard(
        name="차명계좌 추적", description="타인 명의의 계좌로 숨겨진 수입을 추적합니다. '고의적 누락' 혐의에 2배 피해.",
        cost=3, base_damage=35, tax_type=['법인세', '부가세'],
        text="수십 개의 차명계좌 흐름을 파악했다.",
        special_bonus={'target_method': '고의적 누락', 'multiplier': 2.0, 'bonus_desc': '고의적 누락에 2배 피해'}
    ),
    "a_tier_01": LogicCard(
        name="자금출처조사", description="고액 자산가의 불분명한 자금 출처를 추적하여 증여세를 과세합니다.",
        cost=3, base_damage=60, tax_type=['법인세'], # (원래 증여세지만 법인세로 편입)
        text="수십 개의 차명계좌 흐름을 파악했다."
    ),
    "s_tier_01": LogicCard(
        name="국제거래 과세논리", description="이전가격(TP) 조작, 조세피난처를 이용한 역외탈세를 적발합니다. '자본 거래' 혐의에 2배의 피해를 줍니다.",
        cost=3, base_damage=40, tax_type=['법인세'],
        text="BEPS 프로젝트 보고서를 완벽히 이해했다.",
        special_bonus={'target_method': '자본 거래', 'multiplier': 2.0, 'bonus_desc': '자본 거래에 2배 피해'}
    ),
    "s_tier_02": LogicCard(
        name="조세피난처 역외탈세", description="페이퍼컴퍼니(SPC)를 이용해 소득을 해외로 빼돌린 혐의를 적발합니다. '자본 거래' 혐의에 1.5배 피해.",
        cost=4, base_damage=80, tax_type=['법인세'],
        text="BVI, 케이맨 제도의 SPC 실체를 규명했다.",
        special_bonus={'target_method': '자본 거래', 'multiplier': 1.5, 'bonus_desc': '자본 거래에 1.5배 피해'}
    ),
}

# [조사도구 DB] (변경 없음)
ARTIFACT_DB = {
    "coffee": Artifact(
        name="☕ 믹스 커피 한 박스", 
        description="조사관들의 영원한 친구. 야근의 필수품입니다.",
        effect={"type": "on_turn_start", "value": 1, "subtype": "focus"}
    ),
    "forensic": Artifact(
        name="💻 디지털 포렌식 장비",
        description="삭제된 데이터도 복구해내는 최첨단 장비입니다.",
        effect={"type": "on_battle_start", "value": 0.2, "subtype": "clarity"}
    ),
    "vest": Artifact(
        name="🛡️ 방탄 조끼",
        description="악성 민원인의 위협으로부터 몸을 보호합니다. 전투 시작 시 '보호막' 30을 얻습니다.",
        effect={"type": "on_battle_start", "value": 30, "subtype": "shield"}
    ),
    "plan": Artifact(
        name="📜 완벽한 조사계획서",
        description="조사 착수 전 완벽한 계획은 승리의 지름길입니다. 첫 턴에 카드를 1장 더 뽑습니다.",
        effect={"type": "on_battle_start", "value": 1, "subtype": "draw"}
    )
}

# [기업 DB] (전원 이름 및 설명 수정)
COMPANY_DB = [
    Company(
        name="(주)가나푸드", size="소규모", # (수정)
        description="수도권에 식자재를 납품하는 중소 유통업체. 하지만 사장의 SNS에는 슈퍼카와 명품 사진이 가득하다.", # (수정)
        real_case_desc="[교육] 소규모 법인에서 가장 빈번하게 발생하는 유형입니다. 법인 자금의 사적 유용(업무무관가지급금)은 법인세법상 엄격히 규제되며, 인정 이자 및 지급 이자 손금불산입 등 불이익이 큽니다.", # (수정)
        tax_target=50, 
        team_hp_damage=(5, 10), 
        tactics=[
            EvasionTactic("사주 개인적 사용", "법인카드로 명품 가방, 골프 비용 등을 결제", 30, 0.3, 
                          tax_type='법인세', method_type='고의적 누락'),
            EvasionTactic("증빙 미비 경비", "거래처 물품 제공으로 위장했으나 증빙이 없음", 20, 0.5,
                          tax_type='법인세', method_type='단순 오류')
        ],
        defense_actions=[
            "담당 세무사가 시간을 끌고 있습니다.",
            "관련 증빙을 찾고 있다며 제출을 미룹니다.",
            "자료를 분실했다고 주장합니다."
        ]
    ),
    Company(
        name="㈜넥신 (Nexin)", size="중견기업", # (수정)
        description="최근 급성장한 게임 및 IT 솔루션 기업. 복잡한 지배구조와 관계사 거래 속에 무언가를 숨기고 있다.", # (수정)
        real_case_desc="[교육] N사, K사 등 IT 대기업들은 신종 산업의 과세/면세 구분이 복잡한 점을 이용한 탈루가 많습니다. 또한, 페이퍼컴퍼니를 이용한 관계사 부당 지원은 '부당행위계산부인' 대상입니다.", # (수정)
        tax_target=200, 
        team_hp_damage=(10, 25), 
        tactics=[
            EvasionTactic("과면세 오류", "면세 대상이 아닌 솔루션을 면세로 신고하여 부가세를 탈루함", 80, 0.2,
                          tax_type='부가세', method_type='단순 오류'),
            EvasionTactic("관계사 부당 지원", "대표이사 가족 소유의 페이퍼컴퍼니에 용역비를 과다 지급함", 120, 0.1,
                          tax_type='법인세', method_type='자본 거래')
        ],
        defense_actions=[
            "유능한 회계법인이 방어 논리를 준비중입니다.",
            "관련 자료가 서버에서 삭제되었다고 주장합니다.",
            "조사관의 태도를 문제삼아 상부에 민원을 제기했습니다."
        ]
    ),
    Company(
        name="(주)한늠석유 (자료상)", size="중견기업", # (유지)
        description="전형적인 '자료상' 업체. 가짜 석유를 유통시키며 실물 거래 없이 허위 세금계산서만을 발행, 부가세를 포탈하고 있다.", # (수정)
        real_case_desc="[교육] '가짜 석유' 유통 사건에서 빈번하게 등장하는 '자료상'은 국가 세수 기반을 무너뜨리는 심각한 범죄입니다. 허위 세금계산서를 받아 비용을 부풀린 매입 기업도 공범으로 처벌받습니다.", # (유지)
        tax_target=300, 
        team_hp_damage=(15, 30),
        tactics=[
            EvasionTactic("허위 세금계산서 발행", "실물 없이 세금계산서만 발행하여 부가세 매입세액 부당 공제", 200, 0.3, 
                          tax_type='부가세', method_type='고의적 누락'),
            EvasionTactic("가공 경비 계상", "허위 인건비, 경비 계상으로 법인 소득 축소", 100, 0.5,
                          tax_type='법인세', method_type='고의적 누락')
        ],
        defense_actions=[
            "대표이사가 잠적했습니다.",
            "사무실이 텅 비어있습니다. (페이퍼컴퍼니)",
            "대포폰과 대포통장만 발견됩니다."
        ]
    ),
    Company(
        name="㈜삼숭물산 (Samsoong)", size="대기업", # (수정)
        description="수십 개의 계열사를 거느린 대한민국 최고의 대기업. 순환출자 구조가 복잡하며, 총수 일가의 경영권 승계 문제가 항상 이슈가 된다.", # (수정)
        real_case_desc="[교육] S그룹, H그룹 등 대기업들은 복잡한 '자본 거래' (주식 이동, 불공정 합병, 일감 몰아주기)를 통해 경영권을 승계하며 세금을 회피하는 경우가 많습니다. 이는 국세청의 최고 난이도 조사 대상입니다.", # (유지)
        tax_target=1000, 
        team_hp_damage=(20, 40), 
        tactics=[
            EvasionTactic("일감 몰아주기", "총수 일가 소유 회사에 고가로 용역을 발주함", 500, 0.1,
                          tax_type='법인세', method_type='자본 거래'),
            EvasionTactic("가공 세금계산서 수취", "실물 거래 없이 세금계산서만 받아 비용을 부풀림", 300, 0.0,
                          tax_type='부가세', method_type='고의적 누락'),
            EvasionTactic("불공정 합병", "계열사 간 불공정 합병 비율로 경영권을 편법 승계함", 200, 0.0,
                          tax_type='법인세', method_type='자본 거래')
        ],
        defense_actions=[
            "대형 로펌 '광장'이 조사 대응을 시작합니다.",
            "언론에 '무리한 세무조사'라며 기사를 내보냈습니다.",
            "국회의원을 통해 조사 중단 압력을 넣고 있습니다."
        ]
    ),
    Company(
        name="구갈 코리아(유) (Googal)", size="외국계", # (수정)
        description="미국에 본사를 둔 다국적 IT 기업의 한국 지사. 국내에서 막대한 이익을 얻지만, '이전가격(TP)' 조작을 통해 소득을 해외로 이전시킨 혐의가 짙다.", # (수정)
        real_case_desc="[교육] G사, A사 등 다국적 IT 기업들은 '이전가격(TP)' 조작(경영자문료, 라이선스비 과다 지급)을 통해 국내 소득을 고의로 축소하는 경우가 많습니다. 이는 'BEPS' 프로젝트 등 국제적 공조로 대응하고 있습니다.", # (수정)
        tax_target=800, 
        team_hp_damage=(15, 30),
        tactics=[
            EvasionTactic("이전가격(TP) 조작", "본사에 경영자문료, 라이선스비를 과다 지급하여 국내 이익을 축소", 500, 0.1,
                          tax_type='법인세', method_type='자본 거래'),
            EvasionTactic("고정사업장 미신고", "국내에 실질적 사업장이 있으나 신고하지 않고 세금을 회피", 300, 0.2,
                          tax_type='법인세', method_type='고의적 누락')
        ],
        defense_actions=[
            "미국 본사에서 회계 자료 제출을 거부합니다.",
            "조세 조약에 근거한 상호 합의(MAP)를 신청하겠다고 압박합니다.",
            "자료를 영어로만 제출하며 번역을 지연시킵니다."
        ]
    ),
    Company(
        name="(주)씨두해운 (C-Doo)", size="대기업", # (유지)
        description="유명한 '선백왕'이 운영하는 해운사. 조세피난처에 설립한 다수의 페이퍼컴퍼니를 이용해 막대한 세금을 탈루한 혐의가 있다.", # (유지)
        real_case_desc="[교육] '선박왕' C해운 사건은 조세피난처(BVI 등)에 설립된 페이퍼컴퍼니(SPC)를 이용해 수천억 원의 소득을 은닉한 대표적인 역외탈세 사건입니다. 역외탈세는 국제 공조가 필수적입니다.", # (수정)
        tax_target=1500, 
        team_hp_damage=(25, 45),
        tactics=[
            EvasionTactic("역외탈세 (SPC)", "BVI 등 조세피난처 SPC를 통해 국내 소득을 은닉", 1000, 0.1, 
                          tax_type='법인세', method_type='자본 거래'),
            EvasionTactic("선박 취득가액 조작", "선박을 저가에 양도하고 차액을 은닉", 500, 0.2,
                          tax_type='법인세', method_type='고의적 누락')
        ],
        defense_actions=[
            "해외 본사에서 자료 협조를 거부합니다.",
            "선박 거래 자료가 이중으로 작성되었습니다.",
            "국내 법무팀이 대응을 지연시킵니다."
        ]
    ),
]


# --- 3. 게임 상태 초기화 및 관리 ---

def initialize_game():
    """새 게임 시작 (시작 팀 변경)"""
    
    # (수정) 시작 팀 변경 (han, kim, park -> han, kim, park_j)
    start_team = [TAX_MAN_DB["han"], TAX_MAN_DB["kim"], TAX_MAN_DB["park"]]
    st.session_state.player_team = start_team
    
    start_deck = [LOGIC_CARD_DB["basic_01"]] * 3 + [LOGIC_CARD_DB["basic_02"]] * 2 + [LOGIC_CARD_DB["b_tier_04"]] * 2 + [LOGIC_CARD_DB["c_tier_03"]] * 1 + [LOGIC_CARD_DB["c_tier_02"]] * 2
    st.session_state.player_deck = random.sample(start_deck, len(start_deck)) 
    
    st.session_state.player_hand = [] 
    st.session_state.player_discard = [] 
    st.session_state.player_artifacts = [ARTIFACT_DB["coffee"]] 
    
    st.session_state.team_max_hp = sum(member.hp for member in start_team)
    st.session_state.team_hp = st.session_state.team_max_hp
    st.session_state.team_shield = 0 
    
    st.session_state.player_focus_max = sum(member.focus for member in start_team)
    st.session_state.player_focus_current = st.session_state.player_focus_max
    st.session_state.current_battle_company = None
    st.session_state.battle_log = []
    st.session_state.selected_card_index = None 
    st.session_state.bonus_draw = 0 
    
    st.session_state.game_state = "MAP" 
    st.session_state.current_stage_level = 0
    st.session_state.total_collected_tax = 0 


# --- 4. 게임 로직 함수 --- (대부분 변경 없음, calculate_card_cost / execute_attack 일부 수정)

def start_player_turn():
    """플레이어 턴 시작"""
    
    base_focus = sum(member.focus for member in st.session_state.player_team)
    st.session_state.player_focus_current = base_focus
    
    if "임항수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current += 1
        log_message("✨ [기획 조사] 효과로 집중력 +1!", "info")

    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_turn_start" and artifact.effect["subtype"] == "focus":
            st.session_state.player_focus_current += artifact.effect["value"]
            log_message(f"✨ {artifact.name} 효과로 집중력 +{artifact.effect['value']}!", "info")
            
    st.session_state.player_focus_max = st.session_state.player_focus_current 

    cards_to_draw = 5 + st.session_state.get('bonus_draw', 0)
    if st.session_state.get('bonus_draw', 0) > 0:
        log_message(f"✨ {ARTIFACT_DB['plan'].name} 효과로 카드 {st.session_state.bonus_draw}장 추가 드로우!", "info")
        st.session_state.bonus_draw = 0 
        
    draw_cards(cards_to_draw)
    log_message("--- 플레이어 턴 시작 ---")
    st.session_state.turn_first_card_played = True 
    st.session_state.selected_card_index = None 

def draw_cards(num_to_draw):
    """덱에서 카드를 뽑아 손으로 가져옵니다."""
    drawn_cards = []
    for _ in range(num_to_draw):
        if not st.session_state.player_deck:
            if st.session_state.player_discard:
                log_message("덱이 비어, 버린 카드를 섞습니다.")
                st.session_state.player_deck = random.sample(st.session_state.player_discard, len(st.session_state.player_discard))
                st.session_state.player_discard = []
            else:
                log_message("경고: 더 이상 뽑을 카드가 없습니다!", "error")
                break
        
        card = st.session_state.player_deck.pop()
        drawn_cards.append(card)
    
    st.session_state.player_hand.extend(drawn_cards)
    check_draw_cards_in_hand()


def check_draw_cards_in_hand():
    """손에 드로우 효과 카드가 있는지 확인하고 즉시 발동"""
    while True:
        card_to_play = None
        card_index = -1
        
        for i, card in enumerate(st.session_state.player_hand):
            if card.special_effect and card.special_effect.get("type") == "draw":
                card_to_play = card
                card_index = i
                break 
        
        if card_to_play:
            log_message(f"✨ [{card_to_play.name}] 효과 발동! 카드 {card_to_play.special_effect.get('value', 0)}장을 뽑습니다.", "info")
            
            draw_value = card_to_play.special_effect.get('value', 0)
            if "조용균" in [m.name for m in st.session_state.player_team] and card_to_play.name == "법령 재검토":
                 log_message("✨ [세법 교본] 효과로 카드 1장 추가 드로우!", "info")
                 draw_value *= 2

            draw_cards(draw_value)
            st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))

        else:
            break 


def select_card_to_play(card_index):
    """플레이어가 카드를 '선택'"""
    if 'player_hand' not in st.session_state or card_index >= len(st.session_state.player_hand):
        st.toast("오류: 유효하지 않은 카드입니다.", icon="🚨")
        return
        
    card = st.session_state.player_hand[card_index]
    cost_to_pay = calculate_card_cost(card)

    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠")
        return
    
    st.session_state.selected_card_index = card_index
    st.rerun() 

def cancel_card_selection():
    """선택한 카드 취소"""
    st.session_state.selected_card_index = None
    st.rerun()

def calculate_card_cost(card):
    """카드의 실제 소모 비용 계산 (능력 적용)"""
    cost_to_pay = card.cost
    
    # '백용후' 능력 (데이터 카드)
    if "백용후" in [m.name for m in st.session_state.player_team] and ('데이터' in card.name or '분석' in card.name): # (간이 판별)
        cost_to_pay = max(0, cost_to_pay - 1)

    # '박지현' 능력 (첫 분석/설득 카드)
    card_type_match = ('분석' in card.name or '판례' in card.name or '법령' in card.name) # (간이 판별)
    if "박지현" in [m.name for m in st.session_state.player_team] and st.session_state.get('turn_first_card_played', True) and card_type_match:
        cost_to_pay = max(0, cost_to_pay - 1)
        
    return cost_to_pay

def execute_attack(card_index, tactic_index):
    """선택한 카드로 선택한 혐의를 '공격 실행' (보너스 로직 수정)"""
    
    if card_index is None or card_index >= len(st.session_state.player_hand) or tactic_index >= len(st.session_state.current_battle_company.tactics):
        st.toast("오류: 공격 실행 중 오류가 발생했습니다.", icon="🚨")
        st.session_state.selected_card_index = None
        st.rerun()
        return

    card = st.session_state.player_hand[card_index]
    tactic = st.session_state.current_battle_company.tactics[tactic_index]
    company = st.session_state.current_battle_company

    cost_to_pay = calculate_card_cost(card)

    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠")
        st.session_state.selected_card_index = None 
        st.rerun()
        return
        
    st.session_state.player_focus_current -= cost_to_pay
    
    if st.session_state.get('turn_first_card_played', True):
        st.session_state.turn_first_card_played = False

    # --- 데미지 계산 ---
    damage = card.base_damage
    
    # 1. 캐릭터 기본 능력 보너스 (가산)
    if "이철우" in [m.name for m in st.session_state.player_team] and card.name in ["기본 비용 분석", "단순 경비 처리 오류 지적"]:
        damage += 5
        log_message(f"✨ [기본기] 효과로 적출액 +5!", "info")
    
    if "임항수" in [m.name for m in st.session_state.player_team] and ('분석' in card.name or '자료' in card.name or '추적' in card.name):
        damage += 5
        log_message(f"✨ [기획 조사] 효과로 적출액 +5!", "info")

    # 2. '명확도' 보정 (곱연산)
    clarity_multiplier = 1.0 + tactic.clarity
    
    # 3. '유형 일치' 보너스 (곱연산)
    bonus_multiplier = 1.0
    if card.special_bonus and card.special_bonus.get('target_method') == tactic.method_type:
        bonus_multiplier = card.special_bonus.get('multiplier', 1.0)
        log_message(f"🔥 [{card.name}] 효과 발동! {card.special_bonus.get('bonus_desc')}", "warning")
        
        if "조용균" in [m.name for m in st.session_state.player_team] and card.name == "판례 제시":
             bonus_multiplier *= 2
             log_message("✨ [세법 교본] 효과로 '판례 제시' 보너스 2배!", "info")

    # 4. 캐릭터 특수 능력 보너스 (곱연산)
    if "한중희" in [m.name for m in st.session_state.player_team] and (company.size == "외국계" or tactic.method_type == '자본 거래'):
        bonus_multiplier *= 1.3
        log_message(f"✨ [역외탈세 추적] 효과로 최종 피해 +30%!", "info")
        
    if "서영태" in [m.name for m in st.session_state.player_team] and (company.size == "대기업" or company.size == "외국계") and '법인세' in card.tax_type:
        bonus_multiplier *= 1.2
        log_message(f"✨ [대기업 저격] 효과로 최종 피해 +20%!", "info")


    # 최종 데미지
    final_damage = int(damage * clarity_multiplier * bonus_multiplier)
    
    # --- 공격 실행 ---
    tactic.exposed_amount += final_damage
    company.current_collected_tax += final_damage
    
    log_message(f"▶️ [{card.name}] 카드로 [{tactic.name}] 혐의에 {final_damage}백만원 적출!", "success")
    
    # 5. 특수 효과 처리 (명확도 증가 등)
    if card.special_effect:
        if card.special_effect.get("type") == "clarity_plus":
            clarity_bonus = card.special_effect.get("value", 0)
            
            if "백용후" in [m.name for m in st.session_state.player_team] and '데이터' in card.name:
                clarity_bonus += 0.1
                log_message("✨ [TIS 분석] 효과로 '명확도' 10% 추가 증가!", "info")
                
            tactic.clarity = min(1.0, tactic.clarity + clarity_bonus)
            log_message(f"✨ [{tactic.name}] 혐의의 '명확도'가 {clarity_bonus*100:.0f}% 증가했습니다!", "info")

    if tactic.exposed_amount >= tactic.total_amount and not getattr(tactic, 'is_cleared', False):
        tactic.is_cleared = True 
        log_message(f"🔥 [{tactic.name}] 혐의의 탈루액 전액({tactic.total_amount}백만원)을 적발했습니다!", "warning")
        
        if "벤츠" in card.text: log_message("💬 [현장] '법인소유 벤츠S클래스 차량을 발견했다!'", "info")
        if "압수수색" in card.name: log_message("💬 [현장] '압수수색 중 사무실 책상 밑에서 비밀장부를 확보했다!'", "info")

    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
    st.session_state.selected_card_index = None
    
    check_battle_end()
    st.rerun() 

# --- (이하 로직은 이전 버전과 동일) ---

def end_player_turn():
    """플레이어 턴 종료"""
    st.session_state.player_discard.extend(st.session_state.player_hand)
    st.session_state.player_hand = []
    st.session_state.selected_card_index = None 
    
    log_message("--- 기업 턴 시작 ---")
    
    enemy_turn()

    if not check_battle_end():
        start_player_turn()
        st.rerun() 

def enemy_turn():
    """기업 턴 (보호막 로직)"""
    company = st.session_state.current_battle_company
    
    action_desc = random.choice(company.defense_actions)
    
    min_dmg, max_dmg = company.team_hp_damage
    damage = random.randint(min_dmg, max_dmg)
    
    damage_to_shield = min(st.session_state.get('team_shield', 0), damage)
    damage_to_hp = damage - damage_to_shield
    
    st.session_state.team_shield -= damage_to_shield
    st.session_state.team_hp -= damage_to_hp
    
    if damage_to_shield > 0:
        log_message(f"◀️ [기업] {action_desc} (보호막 -{damage_to_shield}, 팀 체력 -{damage_to_hp}!)", "error")
    else:
        log_message(f"◀️ [기업] {action_desc} (팀 체력 -{damage}!)", "error")


    if company.size == "중견기업" and random.random() < 0.3:
        log_message("💬 [기업] '조사대상 법인은 접대비로 100억원을 지출했으나 증빙을 제시하지 않고있습니다.'", "info")
    if company.size == "대기업" and random.random() < 0.2:
        log_message("💬 [로펌] '김앤장 변호사가 과세 논리에 대한 반박 의견서를 제출했습니다.'", "warning")

def check_battle_end():
    """승리/패배 확인"""
    company = st.session_state.current_battle_company

    if company.current_collected_tax >= company.tax_target:
        bonus = company.current_collected_tax - company.tax_target
        log_message(f"🎉 [조사 승리] 목표 세액 {company.tax_target}백만원 달성!", "success")
        log_message(f"💰 초과 추징액 {bonus}백만원을 보너스로 획득합니다!", "success")
        
        st.session_state.total_collected_tax += company.current_collected_tax
        st.session_state.game_state = "REWARD"
        
        if st.session_state.player_discard:
            last_card_text = st.session_state.player_discard[-1].text
            st.toast(f"승리! \"{last_card_text}\"", icon="🎉")
            
        return True

    if st.session_state.team_hp <= 0:
        st.session_state.team_hp = 0
        log_message("‼️ [조사 중단] 팀원들이 모두 지쳐 더 이상 조사를 진행할 수 없습니다...", "error")
        st.session_state.game_state = "GAME_OVER"
        return True
    
    return False

def start_battle(company_template):
    """전투 시작"""
    company = copy.deepcopy(company_template) 
    
    st.session_state.current_battle_company = company
    st.session_state.game_state = "BATTLE"
    st.session_state.battle_log = [f"--- {company.name} ({company.size}) 세무조사 시작 ---"]
    
    st.session_state.team_shield = 0
    st.session_state.bonus_draw = 0

    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_battle_start":
            if artifact.effect["subtype"] == "clarity":
                clarity_bonus = artifact.effect["value"]
                log_message(f"✨ {artifact.name} 효과로 모든 '탈루 혐의' 명확도 +{clarity_bonus*100:.0f}%!", "info")
                for tactic in company.tactics:
                    tactic.clarity = min(1.0, tactic.clarity + clarity_bonus)
            elif artifact.effect["subtype"] == "shield":
                shield_gain = artifact.effect["value"]
                st.session_state.team_shield += shield_gain
                log_message(f"✨ {artifact.name} 효과로 '보호막' {shield_gain} 획득!", "info")
            elif artifact.effect["subtype"] == "draw":
                st.session_state.bonus_draw += artifact.effect["value"]

    st.session_state.player_deck.extend(st.session_state.player_discard)
    st.session_state.player_deck = random.sample(st.session_state.player_deck, len(st.session_state.player_deck))
    st.session_state.player_discard = []
    st.session_state.player_hand = []

    start_player_turn()

def log_message(message, level="normal"):
    """배틀 로그"""
    color_map = {
        "normal": "",
        "success": "green",
        "warning": "orange",
        "error": "red",
        "info": "blue"
    }
    if level != "normal":
        message = f":{color_map[level]}[{message}]"
        
    st.session_state.battle_log.insert(0, message)
    if len(st.session_state.battle_log) > 20: 
        st.session_state.battle_log.pop()


# --- 5. UI 화면 함수 ---

def show_main_menu():
    """메인 메뉴"""
    st.title("💼 세무조사: 덱빌딩 로그라이크")
    st.markdown("---")
    st.header("국세청에 오신 것을 환영합니다.")
    st.write("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")

    st.image("https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?ixlib.rb-4.0.3&q=80&w=1080", 
             caption="국세청 조사국의 풍경 (상상도)", use_container_width=True)

    if st.button("🚨 조사 시작 (신규 게임)", type="primary", use_container_width=True):
        initialize_game()
        st.rerun() 

    with st.expander("📖 게임 방법 (필독!)", expanded=True):
        st.markdown("""
        **1. 🎯 게임 목표**
        - 당신은 세무조사관 팀을 이끌어, 기업들을 순서대로 조사합니다.
        - 각 기업마다 정해진 **'목표 추징 세액'** 을 달성하면 승리합니다.
        
        **2. ⚔️ 전투 (조사) 방식**
        - **❤️ 팀 체력:** 우리 팀의 생명력입니다. 기업의 '반격'에 의해 감소하며, 0이 되면 패배합니다.
        - **🛡️ 팀 보호막:** 체력보다 먼저 소모되는 임시 HP입니다. 매 전투마다 초기화됩니다.
        - **🧠 집중력:** 매 턴마다 주어지는 자원입니다. '과세논리' 카드를 사용하려면 집중력이 필요합니다.
        - **🃏 과세논리 카드:** 당신의 공격 수단입니다.
        - **🧾 탈루 혐의:** 기업의 HP입니다.
        
        **3. ⚠️ [핵심] 규칙: 세목 일치**
        - 모든 카드와 혐의에는 **'법인세'** 또는 **'부가세'** 태그가 붙어있습니다.
        - **'법인세' 카드는 '법인세' 혐의만** 공격할 수 있습니다.
        - 만약 카드를 선택했는데 혐의 버튼이 **`❌ (세목 불일치)`**로 표시되면, 해당 혐의를 공격할 수 없다는 뜻입니다! 
        - `공통` 또는 `법인세, 부가세` 태그가 붙은 카드는 모두 공격 가능합니다.
        
        **4. ✨ [핵심] 규칙: 유형 보너스**
        - 혐의에는 '고의적 누락', '단순 오류' 등 **'탈루 유형'** 이 있습니다.
        - `현장 압수수색` 카드는 '고의적 누락' 혐의에 2배의 피해를 줍니다.
        - `판례 제시` 카드는 '단순 오류' 혐의에 2배의 피해를 줍니다.
        - 이처럼, **상황에 맞는 카드를 사용하는 것**이 승리의 지름길입니다.
        
        **5. 🖱️ 조작법**
        - **[지도]** 화면에서 '조사 시작' 버튼을 눌러 기업과 전투에 진입합니다.
        - **[전투]** 화면 (플레이어 턴):
            1. 오른쪽 **'내 손 안의 카드'** 탭에서 사용할 카드의 **[선택하기]** 버튼을 누릅니다.
            2. 가운데 **'탈루 혐의 목록'** 에서 공격할 혐의의 **[🎯 (혐의 이름) 공격]** 버튼을 누릅니다. (비활성화된 버튼은 공격 불가)
            3. 집중력이 소모되고, 기업의 '현재 적출 세액'이 오릅니다.
            4. 더 이상 낼 카드가 없으면 **[➡️ 턴 종료]** 버튼을 누릅니다.
        """)

def show_map_screen():
    """맵 선택 화면 (교육용 설명 UI 추가)"""
    st.header(f"📍 조사 지역 (Stage {st.session_state.current_stage_level + 1})")
    st.write("조사할 기업을 선택하십시오.")
    
    # (수정) DB 순서대로 정렬
    sorted_companies = sorted(COMPANY_DB, key=lambda x: x.tax_target)
    
    if st.session_state.current_stage_level < len(sorted_companies):
        company_to_investigate = sorted_companies[st.session_state.current_stage_level]
        
        with st.container(border=True):
            st.subheader(f"🏢 {company_to_investigate.name} ({company_to_investigate.size})")
            st.write(company_to_investigate.description)
            st.warning(f"**예상 턴당 데미지:** {company_to_investigate.team_hp_damage[0]} ~ {company_to_investigate.team_hp_damage[1]} ❤️")
            st.info(f"**목표 추징 세액:** {company_to_investigate.tax_target} 백만원 💰")
            
            with st.expander("Click: 이 기업의 혐의 및 실제 사례 정보 보기"):
                st.info(f"**[교육적 정보]**\n{company_to_investigate.real_case_desc}")
                st.markdown("---")
                st.markdown("**주요 탈루 혐의 (정보)**")
                for tactic in company_to_investigate.tactics:
                    st.markdown(f"- **{tactic.name}** (세목: `{tactic.tax_type}`, 유형: `{tactic.method_type}`)")

            if st.button(f"🚨 {company_to_investigate.name} 조사 시작", type="primary", use_container_width=True):
                start_battle(company_to_investigate)
                st.rerun()
    else:
        st.success("🎉 모든 기업 조사를 완료했습니다! (데모 종료)")
        st.balloons()
        if st.button("🏆 명예의 전당 (다시 시작)"):
            st.session_state.game_state = "MAIN_MENU"
            st.rerun()


def show_battle_screen():
    """핵심 전투 화면 (세목 일치 UI 로직)"""
    if not st.session_state.current_battle_company:
        st.error("오류: 조사 대상 기업 정보가 없습니다.")
        st.session_state.game_state = "MAP"
        st.rerun()
        return

    company = st.session_state.current_battle_company
    
    st.title(f"⚔️ {company.name} 조사 중...")
    st.markdown("---")

    col_left, col_mid, col_right = st.columns([1.2, 1.8, 1.5])

    # --- [왼쪽: 플레이어 팀 정보] ---
    with col_left:
        st.subheader("👨‍💼 우리 팀")
        
        st.metric(label="❤️ 팀 체력", 
                  value=f"{st.session_state.team_hp} / {st.session_state.team_max_hp}")
        
        st.metric(label="🛡️ 팀 보호막", 
                  value=f"{st.session_state.get('team_shield', 0)}")

        st.metric(label="🧠 현재 집중력", 
                  value=f"{st.session_state.player_focus_current} / {st.session_state.player_focus_max}")
        
        st.markdown("---")
        
        for member in st.session_state.player_team:
            with st.expander(f"**{member.name}** ({member.position} / {member.grade}급)"):
                st.write(f"HP: {member.hp}/{member.max_hp}")
                st.write(f"Focus: {member.focus}")
                st.info(f"**{member.ability_name}**: {member.ability_desc}")
                st.caption(f"({member.description})")
        
        st.markdown("---")
        
        st.subheader("🧰 조사도구")
        if not st.session_state.player_artifacts:
            st.write("(보유한 도구가 없습니다)")
        for artifact in st.session_state.player_artifacts:
            st.success(f"**{artifact.name}**: {artifact.description}")

    # --- [가운데: 기업 정보 및 배틀 로그] ---
    with col_mid:
        st.subheader(f"🏢 {company.name} ({company.size})")
        
        st.progress(min(1.0, company.current_collected_tax / company.tax_target), 
                    text=f"💰 목표 세액: {company.current_collected_tax} / {company.tax_target} (백만원)")

        st.markdown("---")
        
        st.subheader("🧾 탈루 혐의 목록")
        
        is_card_selected = st.session_state.get("selected_card_index") is not None
        if is_card_selected:
            selected_card_name = st.session_state.player_hand[st.session_state.selected_card_index].name
            st.info(f"**'{selected_card_name}'** 카드로 공격할 혐의를 선택하세요 🎯")
        
        if not company.tactics:
            st.write("(모든 혐의를 적발했습니다!)")
            
        for i, tactic in enumerate(company.tactics):
            tactic_cleared = tactic.exposed_amount >= tactic.total_amount
            
            with st.container(border=True):
                clarity_text = f"🔎 명확도: {tactic.clarity*100:.0f}%"
                if tactic.clarity >= 1.0:
                    clarity_text = f"🔥 {clarity_text} (최대!)"
                
                st.markdown(f"**{tactic.name}** (`{tactic.tax_type}` / `{tactic.method_type}`)")
                st.caption(f"_{tactic.description}_ | {clarity_text}")
                
                if tactic_cleared:
                    st.progress(1.0, text=f"✅ 적발 완료: {tactic.exposed_amount} / {tactic.total_amount} (백만원)")
                else:
                    st.progress(min(1.0, tactic.exposed_amount / tactic.total_amount),
                                text=f"적발액: {tactic.exposed_amount} / {tactic.total_amount} (백만원)")
                
                if is_card_selected and not tactic_cleared:
                    selected_card = st.session_state.player_hand[st.session_state.selected_card_index]
                    
                    is_match = False
                    if '공통' in selected_card.tax_type:
                        is_match = True
                    elif tactic.tax_type in selected_card.tax_type:
                        is_match = True
                    
                    button_label = f"🎯 **{tactic.name}** 공격"
                    if not is_match:
                        button_label = f"❌ (세목 불일치) {tactic.name}"
                    
                    if st.button(button_label, key=f"attack_tactic_{i}", use_container_width=True, disabled=not is_match):
                        execute_attack(st.session_state.selected_card_index, i)

        st.markdown("---")

        st.subheader("📋 조사 기록 (로그)")
        log_container = st.container(height=300, border=True)
        for log in st.session_state.battle_log:
            log_container.markdown(log)

    # --- [오른쪽: 플레이어 카드 및 행동] ---
    with col_right:
        st.subheader("🕹️ 행동")
        
        if st.session_state.get("selected_card_index") is not None:
            if st.button("❌ 공격 취소", use_container_width=True, type="secondary"):
                cancel_card_selection()
        else:
            if st.button("➡️ 턴 종료", use_container_width=True, type="primary"):
                end_player_turn()
                st.rerun() 

        st.markdown("---")

        tab1, tab2 = st.tabs(["🃏 내 손 안의 카드", f"📚 덱({len(st.session_state.player_deck)})/버린 덱({len(st.session_state.player_discard)})"])

        with tab1:
            if not st.session_state.player_hand:
                st.write("(손에 쥔 카드가 없습니다)")
            
            is_card_selected = st.session_state.get("selected_card_index") is not None

            for i, card in enumerate(st.session_state.player_hand):
                if card.special_effect and card.special_effect.get("type") == "draw":
                    continue

                cost_to_pay = calculate_card_cost(card)
                can_afford = st.session_state.player_focus_current >= cost_to_pay
                card_color = "blue" if can_afford else "red"
                
                is_this_card_selected = (st.session_state.get("selected_card_index") == i)

                with st.container(border=True):
                    if is_this_card_selected:
                        st.markdown(f"**🎯 {card.name}** | :{card_color}[비용: {cost_to_pay} 🧠] (선택됨)")
                    else:
                        st.markdown(f"**{card.name}** | :{card_color}[비용: {cost_to_pay} 🧠]")
                        
                    st.caption(f"세목: `{'`, `'.join(card.tax_type)}`")
                    st.write(card.description)
                    st.write(f"**기본 적출액:** {card.base_damage} 백만원")
                    
                    if card.special_effect:
                         if card.special_effect.get("type") == "clarity_plus":
                            st.write(f"**특수효과:** 명확도 +{card.special_effect.get('value')*100:.0f}%")
                    if card.special_bonus:
                        st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")
                    
                    if st.button(f"선택하기: {card.name}", key=f"play_card_{i}", 
                                use_container_width=True, 
                                disabled=(not can_afford or is_card_selected)):
                        select_card_to_play(i)
        
        with tab2:
            with st.expander("📚 덱 보기"):
                card_counts = {}
                for card in st.session_state.player_deck:
                    card_counts[card.name] = card_counts.get(card.name, 0) + 1
                for name in sorted(card_counts.keys()):
                    st.write(f"- {name} x {card_counts[name]}")
            with st.expander("🗑️ 버린 덱 보기"):
                card_counts = {}
                for card in st.session_state.player_discard:
                    card_counts[card.name] = card_counts.get(card.name, 0) + 1
                for name in sorted(card_counts.keys()):
                    st.write(f"- {name} x {card_counts[name]}")


def show_reward_screen():
    """보상 화면"""
    st.header("🎉 조사 승리!")
    st.balloons()
    
    company = st.session_state.current_battle_company
    st.success(f"**{company.name}** 조사 완료. 총 {company.current_collected_tax}백만원을 추징했습니다.")
    st.markdown("---")

    st.subheader("🎁 보상을 선택하세요 (카드 3장 중 1개)")

    if 'reward_cards' not in st.session_state or not st.session_state.reward_cards:
        all_cards = list(LOGIC_CARD_DB.values())
        reward_pool = [c for c in all_cards if c.cost > 0 or (c.cost == 0 and not c.special_effect)]
        st.session_state.reward_cards = random.sample(reward_pool, min(len(reward_pool), 3))

    cols = st.columns(len(st.session_state.reward_cards))
    
    for i, card in enumerate(st.session_state.reward_cards):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{card.name}** | 비용: {card.cost} 🧠")
                st.caption(f"세목: `{'`, `'.join(card.tax_type)}`")
                st.write(card.description)
                st.info(f"**기본 적출액:** {card.base_damage} 백만원")
                if card.special_effect:
                    if card.special_effect.get("type") == "clarity_plus":
                        st.warning(f"**특수효과:** 명확도 +{card.special_effect.get('value')*100:.0f}%")
                if card.special_bonus:
                    st.warning(f"**보너스:** {card.special_bonus.get('bonus_desc')}")

                
                if st.button(f"선택: {card.name}", key=f"reward_{i}", use_container_width=True, type="primary"):
                    st.session_state.player_deck.append(card)
                    st.toast(f"[{card.name}] 카드를 덱에 추가했습니다!", icon="🃏")
                    
                    del st.session_state.reward_cards
                    st.session_state.game_state = "MAP"
                    st.session_state.current_stage_level += 1
                    
                    heal_amount = int(st.session_state.team_max_hp * 0.3) 
                    st.session_state.team_hp = min(st.session_state.team_max_hp, st.session_state.team_hp + heal_amount)
                    st.toast(f"팀원들이 휴식을 취했습니다. (체력 +{heal_amount})", icon="❤️")
                    
                    st.rerun()

def show_game_over_screen():
    """게임 오버 화면"""
    st.header("... 조사가 중단되었습니다 ...")
    st.error("팀원들의 체력이 모두 소진되어 더 이상 조사를 진행할 수 없습니다.")
    
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax} 백만원")
    st.metric("진행한 스테이지", f"📍 {st.session_state.current_stage_level + 1}")
    
    st.image("https://images.unsplash.com/photo-1554224155-16954a151120?ixlib.rb-4.0.3&q=80&w=1080", 
             caption="지친 조사관들...", use_container_width=True)

    if st.button("다시 도전하기", type="primary", use_container_width=True):
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()

def show_player_status_sidebar():
    """사이드바"""
    with st.sidebar:
        st.title("👨‍💼 조사팀 현황")
        st.metric("💰 현재까지 총 추징 세액", f"{st.session_state.total_collected_tax} 백만원")
        st.metric("❤️ 현재 팀 체력", f"{st.session_state.team_hp} / {st.session_state.team_max_hp}")
        
        if st.session_state.game_state == "BATTLE":
            st.metric("🛡️ 현재 팀 보호막", f"{st.session_state.get('team_shield', 0)}")
            
        st.markdown("---")
        
        st.subheader("팀원")
        for member in st.session_state.player_team:
            st.write(f"- **{member.name}** ({member.grade}급)")
        
        total_cards = len(st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand)
        st.subheader(f"보유 덱 ({total_cards}장)")
        
        with st.expander("덱 구성 보기"):
            deck_list = st.session_state.player_deck + st.session_state.player_discard + st.session_state.player_hand
            card_counts = {}
            for card in deck_list:
                card_counts[card.name] = card_counts.get(card.name, 0) + 1
            for name in sorted(card_counts.keys()):
                st.write(f"- {name} x {card_counts[name]}")

        st.markdown("---")
        st.subheader("🧰 보유 도구")
        if not st.session_state.player_artifacts:
            st.write("(없음)")
        for artifact in st.session_state.player_artifacts:
            st.success(f"- {artifact.name}")
        
        st.markdown("---")
        if st.button("게임 포기 (메인 메뉴로)", use_container_width=True):
            st.session_state.game_state = "MAIN_MENU"
            st.rerun()


# --- 6. 메인 실행 로직 ---

def main():
    st.set_page_config(page_title="세무조사 덱빌딩", layout="wide", initial_sidebar_state="expanded")

    if 'game_state' not in st.session_state:
        st.session_state.game_state = "MAIN_MENU"

    if st.session_state.game_state == "MAIN_MENU":
        show_main_menu()
    
    elif st.session_state.game_state == "MAP":
        show_map_screen()
    
    elif st.session_state.game_state == "BATTLE":
        show_battle_screen()
        
    elif st.session_state.game_state == "REWARD":
        show_reward_screen()
        
    elif st.session_state.game_state == "GAME_OVER":
        show_game_over_screen()

    if st.session_state.game_state not in ["MAIN_MENU", "GAME_OVER"]:
        show_player_status_sidebar()

if __name__ == "__main__":
    main()
