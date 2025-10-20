import streamlit as st
import random
import copy # 기업 객체 복사를 위해 추가

# --- 1. 기본 데이터 구조 정의 ---
# (이전과 동일)
class Card:
    """모든 카드의 기본이 되는 클래스"""
    def __init__(self, name, description, cost):
        self.name = name
        self.description = description
        self.cost = cost # 카드를 내는 데 필요한 '집중력' 또는 팀 합류 '비용'

class TaxManCard(Card):
    """조사관 카드 클래스 (플레이어 캐릭터)"""
    def __init__(self, name, grade, position, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost)
        self.grade = grade # S, A, B, C 급
        self.position = position # 팀장, 조사반장, 일반조사관
        self.hp = hp # 체력 (팀 전체 체력에 기여)
        self.max_hp = hp
        
        # 기본 능력치
        self.focus = focus # 집중력 (매 턴 회복되는 자원)
        self.analysis = analysis # 분석력
        self.persuasion = persuasion # 설득력
        self.evidence = evidence # 증거발견
        self.data = data # 데이터수집
        
        self.ability_name = ability_name # 고유 능력 이름
        self.ability_desc = ability_desc # 고유 능력 설명

class LogicCard(Card):
    """과세논리 카드 클래스 (공격 카드)"""
    def __init__(self, name, description, cost, base_damage, logic_type, text):
        super().__init__(name, description, cost)
        self.base_damage = base_damage # 기본 적출 세액 (백만원 단위)
        self.logic_type = logic_type # '분석력', '설득력', '데이터수집' 등 이 카드가 기반하는 능력치
        self.text = text # 승리 시 얻는 텍스트 ("법인세법 18조를 습득했다!")

class EvasionTactic:
    """탈루 혐의 클래스 (기업의 HP)"""
    def __init__(self, name, description, total_amount, clarity):
        self.name = name
        self.description = description
        self.total_amount = total_amount # 총 탈루액 (최대 HP)
        self.exposed_amount = 0 # 현재 드러난 탈루액 (현재 HP)
        self.clarity = clarity # 명확도 (0.0 ~ 1.0) - 명확도가 높을수록 더 큰 피해를 줌

class Company:
    """기업 클래스 (적)"""
    def __init__(self, name, size, description, tax_target, team_hp_damage, tactics, defense_actions):
        self.name = name
        self.size = size # 소규모, 중견, 대기업, 외국계
        self.description = description
        self.tax_target = tax_target # 목표 추징 세액 (승리 조건)
        self.team_hp_damage = team_hp_damage # 턴 당 팀 체력 데미지 (최소, 최대)
        self.current_collected_tax = 0 # 현재까지 누적 적출 세액
        self.tactics = tactics # 보유한 탈루 혐의 리스트
        self.defense_actions = defense_actions # 방어/반격 행동 패턴

class Artifact:
    """조사도구 클래스 (유물)"""
    def __init__(self, name, description, effect):
        self.name = name
        self.description = description
        self.effect = effect # 'on_battle_start', 'on_turn_start' 등 효과

# --- 2. 게임 데이터베이스 (DB) ---

# [조사관 DB] (신규 2명 추가)
TAX_MAN_DB = {
    "choo": TaxManCard(
        name="추징수", grade="S", position="팀장", cost=0, hp=150, focus=4, analysis=10, persuasion=10, evidence=10, data=10,
        description="국세청의 살아있는 전설, '추징의 신'. 그가 맡은 조사는 단 한 건의 불복도 없이 완벽하게 종결된다고 한다. 모든 능력치가 완벽에 가깝다.",
        ability_name="[신속 정확]", ability_desc="매 턴 '집중력'을 1 추가로 얻습니다. '분석력'과 '데이터수집' 능력치가 2배로 적용됩니다.(미구현)"
    ),
    "han": TaxManCard(
        name="한중일", grade="A", position="팀장", cost=0, hp=100, focus=3, analysis=9, persuasion=6, evidence=8, data=9,
        description="국제조세의 베테랑. 조세피난처를 이용한 역외탈세 추적의 1인자. 날카로운 분석력으로 허를 찌른다.",
        ability_name="[역외탈세 추적]", ability_desc="'외국계 기업' 상대 시 모든 '과세논리' 카드의 최종 적출세액 +20%."
    ),
    "kim": TaxManCard(
        name="김철두", grade="B", position="조사반장", cost=0, hp=120, focus=3, analysis=6, persuasion=8, evidence=9, data=5,
        description="포기를 모르는 불굴의 현장 조사관. 압수수색 현장에서 비밀장부를 귀신같이 찾아내는 것으로 유명하다.",
        ability_name="[압수수색]", ability_desc="'조사' 단계(미구현)에서 낮은 확률로 '결정적 증거' 카드를 즉시 획득."
    ),
    "park": TaxManCard(
        name="박지혜", grade="C", position="일반조사관", cost=0, hp=80, focus=4, analysis=7, persuasion=5, evidence=6, data=7,
        description="세무대학을 수석으로 졸업한 엘리트 신입. '걸어다니는 법전'. 이론은 완벽하나 현장 경험은 부족하다.",
        ability_name="[법리 검토]", ability_desc="매 턴 처음 사용하는 '과세논리' 카드의 '집중력' 소모 1 감소."
    ),
    "lee": TaxManCard(
        name="이신입", grade="C", position="일반조사관", cost=0, hp=90, focus=3, analysis=5, persuasion=5, evidence=5, data=5,
        description="이제 막 발령받은 신입 조사관. 열정은 넘치지만 아직 모든 것이 서툴다. 하지만 기본기는 탄탄하다.",
        ability_name="[기본기]", ability_desc="'기본 소득세법 분석'과 '단순 경비 처리 오류 지적' 카드의 기본 적출액 +3."
    )
}

# [과세논리 카드 DB] (신규 3종 추가)
LOGIC_CARD_DB = {
    "c_tier_01": LogicCard(
        name="단순 자료 대사", description="매입/매출 자료를 단순 비교하여 불일치 내역을 찾아냅니다.",
        cost=0, base_damage=3, logic_type="data",
        text="자료 대사의 기본을 익혔다."
    ),
    "basic_01": LogicCard(
        name="기본 소득세법 분석", description="가장 기본적인 세법을 적용하여 소득 누락분을 찾아냅니다.",
        cost=1, base_damage=5, logic_type="analysis",
        text="소득세법 기본 조항을 분석했다."
    ),
    "basic_02": LogicCard(
        name="단순 경비 처리 오류 지적", description="증빙이 미비한 간단한 경비 처리를 지적합니다.",
        cost=1, base_damage=6, logic_type="evidence",
        text="증빙자료 대조의 기본을 익혔다."
    ),
    "corp_01": LogicCard(
        name="접대비 한도 초과", description="법정 한도를 초과한 접대비를 손금불산입합니다.",
        cost=2, base_damage=15, logic_type="analysis",
        text="법인세법 18조(접대비)를 습득했다."
    ),
    "corp_02": LogicCard(
        name="업무 무관 자산 비용 처리", description="대표이사의 개인 차량 유지비 등 업무와 무관한 비용을 적발합니다.",
        cost=2, base_damage=20, logic_type="evidence",
        text="법인소유 벤츠 S클래스 차량의 운행일지를 확보했다!"
    ),
    "b_tier_01": LogicCard(
        name="금융거래 분석", description="의심스러운 자금 흐름을 포착하여 차명계좌를 추적합니다.",
        cost=2, base_damage=30, logic_type="data",
        text="FIU 금융정보 분석 기법을 습득했다."
    ),
    "spec_01": LogicCard(
        name="관계사 부당 지원 (저가 양수)", description="특수 관계사에게 자산을 시가보다 현저히 낮게 양도한 사실을 밝혀냅니다.",
        cost=3, base_damage=50, logic_type="data",
        text="조특법 시행령 30개 조문을 분석했다."
    ),
    "s_tier_01": LogicCard(
        name="국제거래 과세논리", description="이전가격(TP) 조작, 조세피난처를 이용한 역외탈세를 적발합니다.",
        cost=3, base_damage=70, logic_type="analysis",
        text="BEPS 프로젝트 보고서를 완벽히 이해했다."
    ),
}

# [조사도구 DB]
ARTIFACT_DB = {
    "coffee": Artifact(
        name="☕ 믹스 커피 한 박스", 
        description="조사관들의 영원한 친구. 야근의 필수품입니다.",
        effect={"type": "on_turn_start", "value": 1} # 매 턴 시작 시 집중력 +1
    ),
    "forensic": Artifact(
        name="💻 디지털 포렌식 장비",
        description="삭제된 데이터도 복구해내는 최첨단 장비입니다.",
        effect={"type": "on_battle_start", "value": 0.2} # 전투 시작 시 모든 '탈루 혐의'의 '명확도' +20%
    )
}

# [기업 DB] (신규 2종 추가, HP 데미지 추가)
COMPANY_DB = [
    Company(
        name="(주)가나다 식품", size="소규모",
        description="수도권에 식자재를 납품하는 작은 유통업체. 하지만 사장의 씀씀이가 수상하다.",
        tax_target=50, # 5천만원
        team_hp_damage=(5, 10), # 턴당 5~10 데미지
        tactics=[
            EvasionTactic("사주 개인적 사용", "법인카드로 명품 가방, 골프 비용 등을 결제", 30, 0.3),
            EvasionTactic("증빙 미비 경비", "거래처 물품 제공으로 위장했으나 증빙이 없음", 20, 0.5)
        ],
        defense_actions=[
            "담당 세무사가 시간을 끌고 있습니다.",
            "관련 증빙을 찾고 있다며 제출을 미룹니다.",
            "자료를 분실했다고 주장합니다."
        ]
    ),
    Company(
        name="㈜미래테크", size="중견기업",
        description="최근 급성장한 IT 솔루션 기업. 복잡한 거래 구조 속에 무언가를 숨기고 있다.",
        tax_target=200, # 2억
        team_hp_damage=(10, 25), # 턴당 10~25 데미지
        tactics=[
            EvasionTactic("과면세 오류", "면세 대상이 아닌 솔루션을 면세로 신고하여 부가세를 탈루함", 80, 0.2),
            EvasionTactic("관계사 부당 지원", "대표이사 가족 소유의 페이퍼컴퍼니에 용역비를 과다 지급함", 120, 0.1)
        ],
        defense_actions=[
            "유능한 회계법인이 방어 논리를 준비중입니다.",
            "관련 자료가 서버에서 삭제되었다고 주장합니다.",
            "조사관의 태도를 문제삼아 상부에 민원을 제기했습니다."
        ]
    ),
    Company(
        name="㈜글로벌 홀딩스", size="대기업",
        description="수십 개의 계열사를 거느린 문어발식 대기업. 순환출자 구조가 복잡하며, 로펌의 방어가 철벽같다.",
        tax_target=1000, # 10억
        team_hp_damage=(20, 40), # 턴당 20~40 데미지
        tactics=[
            EvasionTactic("일감 몰아주기", "총수 일가 소유 회사에 고가로 용역을 발주함", 500, 0.1),
            EvasionTactic("자본거래 이용 탈세", "주식 변동을 이용한 편법 증여", 300, 0.0),
            EvasionTactic("불공정 합병", "계열사 간 불공정 합병 비율로 경영권을 편법 승계함", 200, 0.0)
        ],
        defense_actions=[
            "대형 로펌 '광장'이 조사 대응을 시작합니다.",
            "언론에 '무리한 세무조사'라며 기사를 내보냈습니다.",
            "국회의원을 통해 조사 중단 압력을 넣고 있습니다."
        ]
    ),
    Company(
        name="코리아 테크놀로지(유)", size="외국계",
        description="미국에 본사를 둔 다국적 IT 기업의 한국 지사. 이전가격(TP)을 조작하여 국내 소득을 해외로 이전시킨 혐의가 짙다.",
        tax_target=800, # 8억
        team_hp_damage=(15, 30),
        tactics=[
            EvasionTactic("이전가격 조작", "본사에 경영자문료, 라이선스비를 과다 지급하여 국내 이익을 축소", 500, 0.1),
            EvasionTactic("고정사업장 미신고", "국내에 실질적 사업장이 있으나 신고하지 않고 세금을 회피", 300, 0.2)
        ],
        defense_actions=[
            "미국 본사에서 회계 자료 제출을 거부합니다.",
            "조세 조약에 근거한 상호 합의(MAP)를 신청하겠다고 압박합니다.",
            "자료를 영어로만 제출하며 번역을 지연시킵니다."
        ]
    ),
]


# --- 3. 게임 상태 초기화 및 관리 ---

def initialize_game():
    """새 게임 시작 시 st.session_state를 초기화합니다."""
    
    # [플레이어 상태]
    start_team = [TAX_MAN_DB["han"], TAX_MAN_DB["kim"], TAX_MAN_DB["park"]]
    st.session_state.player_team = start_team
    
    start_deck = [LOGIC_CARD_DB["basic_01"]] * 4 + [LOGIC_CARD_DB["basic_02"]] * 4 + [LOGIC_CARD_DB["c_tier_01"]] * 2
    st.session_state.player_deck = random.sample(start_deck, len(start_deck)) # 섞기
    
    st.session_state.player_hand = [] # 현재 손에 쥔 카드
    st.session_state.player_discard = [] # 사용한 카드
    st.session_state.player_artifacts = [ARTIFACT_DB["coffee"]] # 시작 유물
    
    st.session_state.team_max_hp = sum(member.hp for member in start_team)
    st.session_state.team_hp = st.session_state.team_max_hp
    
    # [전투 상태]
    st.session_state.player_focus_max = sum(member.focus for member in start_team)
    st.session_state.player_focus_current = st.session_state.player_focus_max
    st.session_state.current_battle_company = None
    st.session_state.battle_log = []
    st.session_state.selected_card_index = None # (중요) 선택한 카드의 인덱스
    
    # [게임 진행 상태]
    st.session_state.game_state = "MAP" # 'MAIN_MENU', 'MAP', 'BATTLE', 'EVENT', 'REWARD', 'GAME_OVER'
    st.session_state.current_stage_level = 0
    st.session_state.total_collected_tax = 0 # 전체 점수

# --- 4. 게임 로직 함수 ---

def start_player_turn():
    """플레이어 턴 시작 시 처리 (카드 뽑기, 자원 리셋)"""
    
    # 1. 집중력(자원) 리셋
    base_focus = sum(member.focus for member in st.session_state.player_team)
    st.session_state.player_focus_current = base_focus
    
    # '추징수' 능력
    if "추징수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current += 1
        log_message("✨ [신속 정확] 효과로 집중력 +1!", "info")

    # 유물 효과 적용 (e.g., 믹스 커피)
    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_turn_start":
            st.session_state.player_focus_current += artifact.effect["value"]
            log_message(f"✨ {artifact.name} 효과로 집중력 +{artifact.effect['value']}!", "info")
            
    st.session_state.player_focus_max = st.session_state.player_focus_current # 최대치도 업데이트

    # 2. 카드 5장 뽑기
    draw_cards(5)
    log_message("--- 플레이어 턴 시작 ---")
    st.session_state.turn_first_card_played = True # '박지혜' 능력 플래그 리셋
    st.session_state.selected_card_index = None # 카드 선택 초기화

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

def select_card_to_play(card_index):
    """[신규] 플레이어가 카드를 '선택' (UI에서 호출)"""
    if 'player_hand' not in st.session_state or card_index >= len(st.session_state.player_hand):
        st.toast("오류: 유효하지 않은 카드입니다.", icon="🚨")
        return
        
    card = st.session_state.player_hand[card_index]
    
    # 1. 예상 비용 계산 (박지혜 능력 포함)
    cost_to_pay = calculate_card_cost(card)

    # 2. 집중력 비용 체크
    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠")
        return
    
    # 3. 카드를 '선택된' 상태로 변경
    st.session_state.selected_card_index = card_index
    st.rerun() # 화면을 다시 그려서 '공격 대상' 버튼을 표시하게 함

def cancel_card_selection():
    """[신규] 선택한 카드 취소"""
    st.session_state.selected_card_index = None
    st.rerun()

def calculate_card_cost(card):
    """[신규] 카드의 실제 소모 비용 계산 (박지혜 능력 적용)"""
    cost_to_pay = card.cost
    has_park = "박지혜" in [m.name for m in st.session_state.player_team]
    is_first_card = st.session_state.get('turn_first_card_played', True)
    
    if has_park and is_first_card:
        cost_to_pay = max(0, card.cost - 1)
    return cost_to_pay

def execute_attack(card_index, tactic_index):
    """[신규] 선택한 카드로 선택한 혐의를 '공격 실행'"""
    
    # 1. 유효성 검사
    if card_index is None or card_index >= len(st.session_state.player_hand) or tactic_index >= len(st.session_state.current_battle_company.tactics):
        st.toast("오류: 공격 실행 중 오류가 발생했습니다.", icon="🚨")
        st.session_state.selected_card_index = None
        st.rerun()
        return

    card = st.session_state.player_hand[card_index]
    tactic = st.session_state.current_battle_company.tactics[tactic_index]
    company = st.session_state.current_battle_company

    # 2. 비용 계산 및 지불
    cost_to_pay = calculate_card_cost(card)

    if st.session_state.player_focus_current < cost_to_pay:
        st.toast(f"집중력이 부족합니다! (필요: {cost_to_pay})", icon="🧠")
        st.session_state.selected_card_index = None # 선택 취소
        st.rerun()
        return
        
    st.session_state.player_focus_current -= cost_to_pay
    
    # '박지혜' 능력 사용 처리
    if "박지혜" in [m.name for m in st.session_state.player_team] and st.session_state.get('turn_first_card_played', True):
        st.session_state.turn_first_card_played = False

    # 3. 데미지 계산
    damage = card.base_damage
    
    # '이신입' 능력
    if "이신입" in [m.name for m in st.session_state.player_team] and card.name in ["기본 소득세법 분석", "단순 경비 처리 오류 지적"]:
        damage += 3
        log_message(f"✨ [기본기] 효과로 적출액 +3!", "info")
    
    # '한중일' 능력
    if "한중일" in [m.name for m in st.session_state.player_team] and company.size == "외국계":
        damage = int(damage * 1.2)
        log_message(f"✨ [역외탈세 추적] 효과로 적출액 +20%!", "info")

    # 혐의 '명확도'에 따른 데미지 보정 (명확도 50% -> 데미지 x1.5)
    damage_multiplier = 1.0 + tactic.clarity
    final_damage = int(damage * damage_multiplier)

    # 4. 적출세액 누적
    tactic.exposed_amount += final_damage
    company.current_collected_tax += final_damage
    
    log_message(f"▶️ [{card.name}] 카드로 [{tactic.name}] 혐의에 {final_damage}백만원 적출!", "success")
    
    if tactic.exposed_amount >= tactic.total_amount and not getattr(tactic, 'is_cleared', False):
        tactic.is_cleared = True # 중복 로그 방지
        log_message(f"🔥 [{tactic.name}] 혐의의 탈루액 전액({tactic.total_amount}백만원)을 적발했습니다!", "warning")
        
        # 현실감 있는 로그 추가
        if "벤츠" in card.text: log_message("💬 [현장] '법인소유 벤츠S클래스 차량을 발견했다!'", "info")
        if "비밀장부" in card.text: log_message("💬 [현장] '압수수색 중 사무실 책상 밑에서 비밀장부를 확보했다!'", "info")


    # 5. 카드 이동 (손 -> 버린 덱)
    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index))
    
    # 6. 카드 선택 해제
    st.session_state.selected_card_index = None
    
    # 7. 승리/패배 체크
    check_battle_end()
    
    st.rerun() # 공격 후 화면 즉시 새로고침

def end_player_turn():
    """플레이어 턴 종료 처리"""
    # 1. 손에 남은 카드 모두 버리기
    st.session_state.player_discard.extend(st.session_state.player_hand)
    st.session_state.player_hand = []
    st.session_state.selected_card_index = None # 카드 선택 초기화
    
    log_message("--- 기업 턴 시작 ---")
    
    # 2. 기업 턴 실행
    enemy_turn()

    # 3. 승리/패배 체크
    if not check_battle_end():
        # 전투가 안 끝났으면 플레이어 턴 시작
        start_player_turn()
        st.rerun() # 턴 변경 시 새로고침

def enemy_turn():
    """기업(적)의 턴 로직"""
    company = st.session_state.current_battle_company
    
    # 1. 방어 행동 (랜덤)
    action_desc = random.choice(company.defense_actions)
    
    # 2. 팀 체력 데미지
    min_dmg, max_dmg = company.team_hp_damage
    damage = random.randint(min_dmg, max_dmg)
    st.session_state.team_hp -= damage
    
    log_message(f"◀️ [기업] {action_desc} (팀 체력 -{damage}!)", "error")

    # 현실감 있는 로그 추가
    if company.size == "중견기업" and random.random() < 0.3:
        log_message("💬 [기업] '조사대상 법인은 접대비로 100억원을 지출했으나 증빙을 제시하지 않고있습니다.'", "info")
    if company.size == "대기업" and random.random() < 0.2:
        log_message("💬 [로펌] '김앤장 변호사가 과세 논리에 대한 반박 의견서를 제출했습니다.'", "warning")

def check_battle_end():
    """전투 승리 또는 패배 조건을 확인합니다."""
    company = st.session_state.current_battle_company

    # 1. 승리 조건: 목표 세액 달성
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

    # 2. 패배 조건: 팀 체력 0
    if st.session_state.team_hp <= 0:
        st.session_state.team_hp = 0
        log_message("‼️ [조사 중단] 팀원들이 모두 지쳐 더 이상 조사를 진행할 수 없습니다...", "error")
        st.session_state.game_state = "GAME_OVER"
        return True
    
    return False

def start_battle(company_template):
    """전투 시작"""
    # (중요) DB 원본이 아닌 복사본으로 전투를 시작해야 함
    company = copy.deepcopy(company_template) 
    
    st.session_state.current_battle_company = company
    st.session_state.game_state = "BATTLE"
    st.session_state.battle_log = [f"--- {company.name} ({company.size}) 세무조사 시작 ---"]
    
    # 유물 효과 적용
    for artifact in st.session_state.player_artifacts:
        if artifact.effect["type"] == "on_battle_start":
            clarity_bonus = artifact.effect["value"]
            log_message(f"✨ {artifact.name} 효과로 모든 '탈루 혐의' 명확도 +{clarity_bonus*100:.0f}%!", "info")
            for tactic in company.tactics:
                tactic.clarity = min(1.0, tactic.clarity + clarity_bonus)

    # 덱 초기화 (버린 덱 -> 덱 -> 섞기)
    st.session_state.player_deck.extend(st.session_state.player_discard)
    st.session_state.player_deck = random.sample(st.session_state.player_deck, len(st.session_state.player_deck))
    st.session_state.player_discard = []
    st.session_state.player_hand = []

    start_player_turn()

def log_message(message, level="normal"):
    """배틀 로그에 메시지를 추가합니다."""
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
    """메인 메뉴 화면 (UI 개선)"""
    st.title("💼 세무조사: 덱빌딩 로그라이크")
    st.markdown("---")
    st.header("국세청에 오신 것을 환영합니다.")
    st.write("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")

    st.image("https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?ixlib=rb-4.0.3&q=80&w=1080", 
             caption="국세청 조사국의 풍경 (상상도)", use_column_width=True)

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
        - **🧠 집중력:** 매 턴마다 주어지는 자원입니다. '과세논리' 카드를 사용하려면 집중력이 필요합니다.
        - **🃏 과세논리 카드:** 당신의 공격 수단입니다. 카드를 내면 '적출 세액'이 누적됩니다.
        - **🧾 탈루 혐의:** 기업의 HP입니다. 각 혐의마다 '총 탈루액'이 정해져 있습니다.
        - **🔎 명확도:** 혐의가 얼마나 명확한지 나타냅니다. 명확도가 높을수록 '과세논리' 카드의 효과가 강력해집니다.
        
        **3. 🖱️ 조작법**
        - **[지도]** 화면에서 '조사 시작' 버튼을 눌러 기업과 전투에 진입합니다.
        - **[전투]** 화면 (플레이어 턴):
            1. 오른쪽 **'내 손 안의 카드'** 탭에서 사용할 카드의 **[선택하기]** 버튼을 누릅니다.
            2. 가운데 **'탈루 혐의 목록'** 에서 방금 선택한 카드로 공격할 혐의의 **[🎯 (혐의 이름) 공격]** 버튼을 누릅니다.
            3. 집중력이 소모되고, 기업의 '현재 적출 세액'이 오릅니다.
            4. (선택 취소: '❌ 공격 취소' 버튼을 누르면 카드가 패로 돌아옵니다.)
            5. 더 이상 낼 카드가 없으면 **[➡️ 턴 종료]** 버튼을 누릅니다.
            6. 기업이 반격하여 '팀 체력'이 감소합니다.
            7. 다시 당신의 턴이 돌아옵니다. (새 카드 5장, 집중력 회복)
        
        **4. 🚀 성장**
        - 전투에서 승리하면 보상을 얻습니다.
        - **새로운 '과세논리' 카드**를 덱에 추가하거나, **'조사도구'(유물)**를 획득하여 팀을 영구적으로 강화할 수 있습니다.
        """)

def show_map_screen():
    """맵 선택 화면"""
    st.header(f"📍 조사 지역 (Stage {st.session_state.current_stage_level + 1})")
    st.write("조사할 기업을 선택하십시오.")
    
    if st.session_state.current_stage_level < len(COMPANY_DB):
        company_to_investigate = COMPANY_DB[st.session_state.current_stage_level]
        
        with st.container(border=True):
            st.subheader(f"🏢 {company_to_investigate.name} ({company_to_investigate.size})")
            st.write(company_to_investigate.description)
            st.warning(f"**예상 턴당 데미지:** {company_to_investigate.team_hp_damage[0]} ~ {company_to_investigate.team_hp_damage[1]} ❤️")
            st.info(f"**목표 추징 세액:** {company_to_investigate.tax_target} 백만원 💰")

            if st.button(f"🚨 {company_to_investigate.name} 조사 시작", type="primary", use_container_width=True):
                start_battle(company_to_investigate)
                st.rerun()
    else:
        st.success("🎉 모든 기업 조사를 완료했습니다! (데모 종료)")
        st.balloons()
        if st.button("🏆 명예의 전당 (다시 시작)"):
            st.session_state.game_state = "MAIN_MENU"
            st.rerun()

    show_player_status_sidebar() # 맵에서도 사이드바 표시

def show_battle_screen():
    """핵심 전투 화면 (UI 대폭 개선)"""
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

        st.metric(label="🧠 현재 집중력", 
                  value=f"{st.session_state.player_focus_current} / {st.session_state.player_focus_max}")
        
        st.markdown("---")
        
        # 팀원 목록
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
        
        # [신규] 카드 선택 시 공격 버튼 표시
        is_card_selected = st.session_state.get("selected_card_index") is not None
        if is_card_selected:
            selected_card_name = st.session_state.player_hand[st.session_state.selected_card_index].name
            st.info(f"**'{selected_card_name}'** 카드로 공격할 혐의를 선택하세요 🎯")
        
        if not company.tactics:
            st.write("(모든 혐의를 적발했습니다!)")
            
        for i, tactic in enumerate(company.tactics):
            tactic_cleared = tactic.exposed_amount >= tactic.total_amount
            
            with st.container(border=True):
                st.markdown(f"**{tactic.name}** (🔎 명확도: {tactic.clarity*100:.0f}%)")
                st.caption(f"_{tactic.description}_")
                
                if tactic_cleared:
                    st.progress(1.0, text=f"✅ 적발 완료: {tactic.exposed_amount} / {tactic.total_amount} (백만원)")
                else:
                    st.progress(min(1.0, tactic.exposed_amount / tactic.total_amount),
                                text=f"적발액: {tactic.exposed_amount} / {tactic.total_amount} (백만원)")
                
                # [신규] 공격 대상 선택 버튼
                if is_card_selected and not tactic_cleared:
                    if st.button(f"🎯 **{tactic.name}** 공격", key=f"attack_tactic_{i}", use_container_width=True):
                        execute_attack(st.session_state.selected_card_index, i)
                        # execute_attack 함수 내부에서 rerun 하므로 여기서는 필요 없음

        st.markdown("---")

        st.subheader("📋 조사 기록 (로그)")
        log_container = st.container(height=300, border=True)
        for log in st.session_state.battle_log:
            log_container.markdown(log)

    # --- [오른쪽: 플레이어 카드 및 행동] ---
    with col_right:
        st.subheader("🕹️ 행동")
        
        if st.session_state.get("selected_card_index") is not None:
             # [신규] 공격 취소 버튼
            if st.button("❌ 공격 취소", use_container_width=True, type="secondary"):
                cancel_card_selection()
        else:
            # 턴 종료 버튼
            if st.button("➡️ 턴 종료", use_container_width=True, type="primary"):
                end_player_turn()
                st.rerun() 

        st.markdown("---")

        # [신규] 탭으로 손/덱 분리
        tab1, tab2 = st.tabs(["🃏 내 손 안의 카드", f"📚 덱({len(st.session_state.player_deck)})/버린 덱({len(st.session_state.player_discard)})"])

        with tab1:
            if not st.session_state.player_hand:
                st.write("(손에 쥔 카드가 없습니다)")
            
            is_card_selected = st.session_state.get("selected_card_index") is not None

            for i, card in enumerate(st.session_state.player_hand):
                cost_to_pay = calculate_card_cost(card)
                can_afford = st.session_state.player_focus_current >= cost_to_pay
                card_color = "blue" if can_afford else "red"
                
                is_this_card_selected = (st.session_state.get("selected_card_index") == i)

                with st.container(border=True):
                    if is_this_card_selected:
                        st.markdown(f"**🎯 {card.name}** | :{card_color}[비용: {cost_to_pay} 🧠] (선택됨)")
                    else:
                        st.markdown(f"**{card.name}** | :{card_color}[비용: {cost_to_pay} 🧠]")
                        
                    st.caption(f"({card.logic_type} 기반)")
                    st.write(card.description)
                    st.write(f"**기본 적출액:** {card.base_damage} 백만원")
                    
                    if st.button(f"선택하기: {card.name}", key=f"play_card_{i}", 
                                use_container_width=True, 
                                disabled=(not can_afford or is_card_selected)): # 비용이 모자라거나, 다른 카드가 이미 선택됨
                        select_card_to_play(i)
        
        with tab2:
            with st.expander("📚 덱 보기"):
                card_counts = {}
                for card in st.session_state.player_deck:
                    card_counts[card.name] = card_counts.get(card.name, 0) + 1
                for name, count in card_counts.items():
                    st.write(f"- {name} x {count}")
            with st.expander("🗑️ 버린 덱 보기"):
                card_counts = {}
                for card in st.session_state.player_discard:
                    card_counts[card.name] = card_counts.get(card.name, 0) + 1
                for name, count in card_counts.items():
                    st.write(f"- {name} x {count}")


def show_reward_screen():
    """전투 승리 후 보상 선택 화면"""
    st.header("🎉 조사 승리!")
    st.balloons()
    
    company = st.session_state.current_battle_company
    st.success(f"**{company.name}** 조사 완료. 총 {company.current_collected_tax}백만원을 추징했습니다.")
    st.markdown("---")

    st.subheader("🎁 보상을 선택하세요 (카드 3장 중 1개)")

    if 'reward_cards' not in st.session_state or not st.session_state.reward_cards:
        # (개선) C급부터 S급까지 골고루 나오도록 가중치 조절
        all_cards = list(LOGIC_CARD_DB.values())
        reward_pool = [c for c in all_cards if c.cost > 0] # 0코스트 C급 카드 제외
        st.session_state.reward_cards = random.sample(reward_pool, min(len(reward_pool), 3))

    cols = st.columns(len(st.session_state.reward_cards))
    
    for i, card in enumerate(st.session_state.reward_cards):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{card.name}** | 비용: {card.cost} 🧠")
                st.caption(f"({card.logic_type} 기반)")
                st.write(card.description)
                st.info(f"**기본 적출액:** {card.base_damage} 백만원")
                
                if st.button(f"선택: {card.name}", key=f"reward_{i}", use_container_width=True, type="primary"):
                    st.session_state.player_deck.append(card)
                    st.toast(f"[{card.name}] 카드를 덱에 추가했습니다!", icon="🃏")
                    
                    del st.session_state.reward_cards
                    st.session_state.game_state = "MAP"
                    st.session_state.current_stage_level += 1
                    
                    # (신규) 다음 스테이지 진입 시 체력 회복
                    heal_amount = int(st.session_state.team_max_hp * 0.3) # 최대 체력의 30% 회복
                    st.session_state.team_hp = min(st.session_state.team_max_hp, st.session_state.team_hp + heal_amount)
                    st.toast(f"팀원들이 휴식을 취했습니다. (체력 +{heal_amount})", icon="❤️")
                    
                    st.rerun()
    
    # TODO: '조사도구' 보상 추가

def show_game_over_screen():
    """[신규] 게임 오버 화면"""
    st.header("... 조사가 중단되었습니다 ...")
    st.error("팀원들의 체력이 모두 소진되어 더 이상 조사를 진행할 수 없습니다.")
    
    st.metric("최종 총 추징 세액", f"💰 {st.session_state.total_collected_tax} 백만원")
    st.metric("진행한 스테이지", f"📍 {st.session_state.current_stage_level + 1}")
    
    st.image("https://images.unsplash.com/photo-1554224155-16954a151120?ixlib=rb-4.0.3&q=80&w=1080", 
             caption="지친 조사관들...", use_column_width=True)

    if st.button("다시 도전하기", type="primary", use_container_width=True):
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()

def show_player_status_sidebar():
    """모든 화면 좌측에 표시될 플레이어 상태 사이드바 (UI 개선)"""
    with st.sidebar:
        st.title("👨‍💼 조사팀 현황")
        st.metric("💰 현재까지 총 추징 세액", f"{st.session_state.total_collected_tax} 백만원")
        st.metric("❤️ 현재 팀 체력", f"{st.session_state.team_hp} / {st.session_state.team_max_hp}")
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
            # 이름순으로 정렬
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

    # 사이드바는 '메인 메뉴' 아닐 때 항상 표시
    if st.session_state.game_state not in ["MAIN_MENU", "GAME_OVER"]:
        show_player_status_sidebar()

if __name__ == "__main__":
    main()
