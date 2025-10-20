import streamlit as st
import random
import copy # 기업 객체 복사를 위해 추가
from enum import Enum # Enum 사용을 위해 추가

# --- 0. Enum(열거형) 정의 ---
# (이전과 동일)
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

# --- 헬퍼 함수: 가독성 개선 ---
def format_krw(amount_in_millions):
    """
    (이전과 동일) 백만원 단위를 '조', '억' 단위의 읽기 쉬운 문자열로 변환합니다.
    """
    if amount_in_millions is None:
        return "N/A"
    try:
        if abs(amount_in_millions) >= 1_000_000:
            return f"{amount_in_millions / 1_000_000:,.1f}조원"
        elif abs(amount_in_millions) >= 10_000:
            return f"{amount_in_millions / 10_000:,.0f}억원"
        elif abs(amount_in_millions) >= 100:
            return f"{amount_in_millions / 100:,.0f}억원"
        else:
            return f"{amount_in_millions:,.0f}백만원"
    except Exception as e:
        return f"{amount_in_millions} (Format Error)"


# --- 1. 기본 데이터 구조 정의 ---
# (이전과 동일)
class Card:
    def __init__(self, name, description, cost):
        self.name = name
        self.description = description
        self.cost = cost

class TaxManCard(Card):
    def __init__(self, name, grade_num, description, cost, hp, focus, analysis, persuasion, evidence, data, ability_name, ability_desc):
        super().__init__(name, description, cost)
        self.grade_num = grade_num
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
    def __init__(self, name, description, cost, base_damage, tax_type: list[TaxType], attack_category: list[AttackCategory], text, special_effect=None, special_bonus=None):
        super().__init__(name, description, cost)
        self.base_damage = base_damage
        self.tax_type = tax_type
        self.attack_category = attack_category
        self.text = text
        self.special_effect = special_effect
        self.special_bonus = special_bonus

class EvasionTactic:
    def __init__(self, name, description, total_amount, tax_type: TaxType | list[TaxType], method_type: MethodType, tactic_category: AttackCategory):
        self.name = name
        self.description = description
        self.total_amount = total_amount
        self.exposed_amount = 0
        self.tax_type = tax_type
        self.method_type = method_type
        self.tactic_category = tactic_category
        self.is_cleared = False

class Company:
    def __init__(self, name, size, description, real_case_desc, revenue, operating_income, tax_target, team_hp_damage, tactics, defense_actions):
        self.name = name
        self.size = size
        self.description = description
        self.real_case_desc = real_case_desc
        self.revenue = revenue
        self.operating_income = operating_income
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
# (이전 코드와 동일 - 캐릭터 정보, 교육 정보 등 업데이트 반영됨)
# ... (TAX_MAN_DB, LOGIC_CARD_DB, ARTIFACT_DB, COMPANY_DB 생략 - 이전 코드와 동일) ...

# --- 3. 게임 상태 초기화 및 관리 ---
# (이전 코드와 동일)
# ... initialize_game ...

# --- 4. 게임 로직 함수 ---

# --- log_message 함수 정의 (가장 먼저) ---
def log_message(message, level="normal"):
    """ 로그 메시지를 st.session_state.battle_log에 추가합니다. """
    # battle_log 키가 없을 경우 초기화 (안전 장치)
    if 'battle_log' not in st.session_state:
        st.session_state.battle_log = []
    # battle_log가 None일 경우 빈 리스트로 초기화 (추가 안정성)
    elif st.session_state.battle_log is None:
        st.session_state.battle_log = []

    color_map = {"normal": "", "success": "green", "warning": "orange", "error": "red", "info": "blue"}
    if level != "normal":
        message = f":{color_map[level]}[{message}]"

    st.session_state.battle_log.insert(0, message)
    if len(st.session_state.battle_log) > 30:
        st.session_state.battle_log.pop()

# (이하 로직 함수들은 이전 버전과 거의 동일)
# ... (start_player_turn, draw_cards, check_draw_cards_in_hand 등등) ...
# ... (start_battle 함수 포함) ...
# ... (go_to_next_stage 등 나머지 로직 함수들) ...

# --- 5. UI 화면 함수 ---

# --- [수정됨] show_main_menu (st.number_input 처리 방식 변경) ---
def show_main_menu():
    st.title("💼 세무조사: 덱빌딩 로그라이크"); st.markdown("---"); st.header("국세청에 오신 것을 환영합니다.")
    st.write("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")

    st.image("https://images.unsplash.com/photo-1497366811353-6870744d04b2?q=80&w=1080",
             caption="세무조사 현장 (상상도)",
             width=400)

    # (수정) st.number_input 처리 방식 변경
    # 위젯 자체에 key를 부여하고, session_state 직접 접근 대신 get 사용
    seed_value = st.session_state.get('seed', 0)
    new_seed = st.number_input(
        "RNG 시드 (0 = 랜덤)",
        value=seed_value,
        step=1,
        key="rng_seed_input", # 위젯 고유 키
        help="0이 아닌 값을 입력하면 동일한 팀 구성과 보상으로 테스트할 수 있습니다."
    )
    # 위젯 값이 변경되었을 경우에만 session_state 업데이트
    if new_seed != seed_value:
        st.session_state.seed = new_seed

    if st.button("🚨 조사 시작 (신규 게임)", type="primary", use_container_width=True):
        current_seed = st.session_state.get('seed', 0) # 업데이트된 seed 값 사용
        if current_seed != 0:
            random.seed(current_seed)
        else:
            random.seed() # 0이면 완전 랜덤

        all_members = list(TAX_MAN_DB.values())
        st.session_state.draft_team_choices = random.sample(all_members, min(len(all_members), 4))

        artifact_keys = list(ARTIFACT_DB.keys())
        chosen_artifact_keys = random.sample(artifact_keys, min(len(artifact_keys), 3))
        st.session_state.draft_artifact_choices = [ARTIFACT_DB[k] for k in chosen_artifact_keys]

        st.session_state.game_state = "GAME_SETUP_DRAFT"
        st.rerun()

    with st.expander("📖 게임 방법 (필독!)", expanded=True):
        st.markdown("""
        **1. 🎯 게임 목표**
        - 무작위 팀(3명)으로 기업들을 조사하여 **'목표 추징 세액'** 을 달성하면 승리.
        **2. ⚔️ 전투 방식**
        - ❤️ **팀 체력:** 0 되면 패배 (주의: 이전보다 낮아짐!). / 🧠 **집중력:** 카드 사용 자원 (매우 적음).
        **3. ⚠️ 패널티 시스템 (중요!)**
        - **1. 세목 불일치:** `법인세` 카드로 `부가세` 혐의 공격 시 실패, **팀 체력 -10**.
        - **2. 유형 불일치:** `비용` 카드로 `수익` 혐의 공격 시 실패, **팀 체력 -5**.
        - 공격 버튼 `⚠️ (불일치)` 경고 주의! (클릭 불가)
        **4. ✨ 유형 보너스**
        - 혐의에는 `고의적 누락`, `단순 오류`, `자본 거래` 등 **'탈루 유형'** 이 있음.
        - `현장 압수수색`은 '고의적 누락'에 2배, `판례 제시`는 '단순 오류'에 2배.
        """)

# (show_setup_draft_screen 이전과 동일)
# ...

# (show_map_screen 이전과 동일)
# ...

# (show_battle_screen 이전과 동일)
# ...

# (show_reward_screen, show_reward_remove_screen 이전과 동일)
# ...

# (show_game_over_screen 이전과 동일)
# ...

# (show_player_status_sidebar 이전과 동일)
# ...

# --- 6. 메인 실행 로직 ---
# --- [수정됨] main (상태 유효성 검사 강화) ---
def main():
    st.set_page_config(page_title="세무조사 덱빌딩", layout="wide", initial_sidebar_state="expanded")

    # 세션 상태 초기화 확인
    if 'game_state' not in st.session_state:
        st.session_state.game_state = "MAIN_MENU"

    current_game_state = st.session_state.get('game_state', "MAIN_MENU") # 안전하게 상태 가져오기

    # (개선) 상태 유효성 검사 강화
    is_state_valid = True
    required_keys = []

    # 각 상태별 필수 키 정의
    if current_game_state == "GAME_SETUP_DRAFT":
        required_keys = ['draft_team_choices', 'draft_artifact_choices']
    elif current_game_state in ["MAP", "BATTLE", "REWARD", "REWARD_REMOVE"]:
        # battle_log 키는 log_message에서 안전하게 생성하므로 제외 가능
        required_keys = ['player_team', 'player_deck', 'player_discard', 'player_hand', 'current_stage_level', 'player_artifacts', 'team_stats', 'company_order']
        if current_game_state == "BATTLE" or current_game_state == "REWARD": # REWARD에서도 company 필요
            required_keys.append('current_battle_company')
    elif current_game_state == "GAME_OVER":
         required_keys = ['total_collected_tax', 'current_stage_level']

    # 필요한 키가 st.session_state에 모두 존재하는지 확인
    if required_keys and not all(key in st.session_state for key in required_keys):
        is_state_valid = False

    # 상태가 유효하지 않으면 메인 메뉴로 리셋
    if not is_state_valid and current_game_state != "MAIN_MENU": # 메인 메뉴 상태 자체는 항상 유효
        st.toast("⚠️ 세션 상태 오류 발생. 게임을 초기화하고 메인 메뉴로 돌아갑니다.")
        # 필수 키 외 불필요한 키 정리 (선택적)
        keys_to_delete = [k for k in st.session_state.keys() if k not in ['game_state', 'seed', 'rng_seed_input']] # game_state, seed 관련 키 제외
        for key in keys_to_delete:
            if key in st.session_state:
                try: # 안전하게 삭제 시도
                    del st.session_state[key]
                except KeyError:
                    pass # 이미 없으면 무시
        st.session_state.game_state = "MAIN_MENU"
        st.rerun()
        return # 메인 메뉴로 리디렉션 후 즉시 종료

    # 상태에 따른 화면 표시 (상태가 유효할 때만)
    sidebar_needed = False # 사이드바 표시 여부 플래그

    if current_game_state == "MAIN_MENU":
        show_main_menu()
    elif current_game_state == "GAME_SETUP_DRAFT":
        show_setup_draft_screen()
    elif current_game_state == "MAP":
        show_map_screen()
        sidebar_needed = True
    elif current_game_state == "BATTLE":
        show_battle_screen()
        sidebar_needed = True
    elif current_game_state == "REWARD":
        show_reward_screen()
        sidebar_needed = True
    elif current_game_state == "REWARD_REMOVE":
        show_reward_remove_screen()
        sidebar_needed = True
    elif current_game_state == "GAME_OVER":
        show_game_over_screen()

    # 사이드바 표시 (필요한 상태이고, 필수 키가 있을 때만)
    sidebar_display_keys = ['player_team', 'team_stats', 'player_artifacts', 'player_deck', 'player_discard', 'player_hand'] # 사이드바 표시에 필요한 키
    if sidebar_needed and all(key in st.session_state for key in sidebar_display_keys):
        show_player_status_sidebar()

if __name__ == "__main__":
    main()
