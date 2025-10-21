# --- [수정됨] 기업 정보 최신화 및 교육 내용 강화 (COMPANY_DB) ---
COMPANY_DB = [
    Company(
        name="(주)가나푸드", size="소규모", revenue=8000, operating_income=800, tax_target=10, team_hp_damage=(5, 12), # 목표 상향
        description="인기 **SNS 인플루언서**가 운영하는 **온라인 쇼핑몰**(식품 유통). 대표는 **고가 외제차**, **명품** 과시.",
        real_case_desc="""[교육] 최근 **온라인 플랫폼 기반 사업자**들의 탈세가 증가하고 있습니다. 주요 유형은 다음과 같습니다:
        * **개인 계좌** 사용: 법인 계좌 대신 대표 또는 가족 명의 계좌로 **매출 대금**을 받아 **매출 누락**.
        * **업무 무관 경비**: 법인 명의 **슈퍼카 리스료**, 대표 개인 **명품 구매 비용**, **가족 해외여행 경비** 등을 법인 비용으로 처리 (**손금 불산입** 및 대표 **상여** 처분 대상).
        * **증빙 미비**: 실제 지출 없이 **가공 경비** 계상 후 증빙 미비.""",
        tactics=[
            EvasionTactic("사주 개인 유용 및 경비", "대표 개인 **명품 구매**(5천만원), **해외여행 경비**(3천만원), **자녀 학원비**(2천만원) 등 총 **1억원**을 법인 비용 처리.", 7, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST), # 금액 상향
            EvasionTactic("매출 누락 (개인 계좌)", "고객으로부터 받은 **현금 매출** 및 **계좌 이체** 대금 중 **3억원**을 대표 개인 계좌로 받아 **매출 신고 누락**.", 3, [TaxType.CORP, TaxType.VAT], MethodType.INTENTIONAL, AttackCategory.REVENUE) # 신규 혐의
        ], defense_actions=["담당 세무사가 '실수' 주장.", "대표가 '개인 돈 썼다'고 항변.", "경리 직원이 '몰랐다' 시전."]
    ),
    Company(
        name="㈜넥신 (Nexin)", size="중견기업", revenue=200000, operating_income=15000, tax_target=100, team_hp_damage=(15, 30), # 스탯 상향
        description="**AI** 및 **메타버스** 기술 기반 **게임/IT 기업**. **정부 R&D 지원** 수혜 및 임직원 **스톡옵션** 다수 부여.",
        real_case_desc="""[교육] 신기술 분야 기업은 **세제 혜택**이 많지만, 이를 악용한 탈루 시도도 빈번합니다:
        * **연구인력개발비 세액공제**: **실제 R&D 참여 인력**이 아닌 **영업직, 관리직** 인건비까지 포함하여 공제 신청 (**부당 공제**). 개발 단계별 **구분 회계** 미비 시 전액 부인될 수도 있음.
        * **국고보조금**: R&D 명목으로 받은 **정부 지원금** 사용처 불분명 또는 **사적 유용** 시 **법인세** 및 **부가세** 추징 가능.
        * **스톡옵션**: **비상장 주식** 가치를 낮게 평가하여 **세금 없이** 임직원(주로 임원)에게 이익 분여 시도 (**소득세** 또는 **증여세** 문제 발생 가능).""",
        tactics=[
            EvasionTactic("R&D 인건비 부당 공제", "**연구개발**과 무관한 **영업/관리직 인건비** 60억원을 **R&D 세액공제** 대상에 포함시켜 **법인세** 부당 공제.", 60, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.COST), # 금액 상향
            EvasionTactic("스톡옵션 저가 행사", "임원에게 부여한 **스톡옵션** 행사 시 **비상장주식 가치**를 외부 평가 없이 **액면가** 수준으로 임의 평가하여 **소득세** 40억원 탈루.", 40, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL)
        ], defense_actions=["회계법인이 '적격 R&D' 의견 제시.", "연구 노트 등 서류 미비.", "스톡옵션 평가는 '정관 규정' 따랐다고 주장."]
    ),
    Company(
        name="(주)한늠석유 (자료상)", size="중견기업", revenue=70000, operating_income=-800, tax_target=150, team_hp_damage=(20, 35), # 스탯 상향
        description="**유류 도매업체**. **유가보조금 부정수급** 및 **허위 세금계산서** 발행 전력 다수.",
        real_case_desc="""[교육] **자료상**은 실제 거래 없이 세금계산서만 사고파는 행위를 통해 국가 재정을 축내는 대표적인 **조세 범죄**입니다. 최근에는 다음과 같은 지능적인 수법이 등장하고 있습니다:
        * **폭탄업체 동원**: 단기간에 **허위 세금계산서**를 대량 발행하고 폐업하는 **폭탄업체** 설립·운영.
        * **세금계산서 양도**: 정상 사업자로부터 세금계산서를 **매입**하여 다른 업체에 **되파는** 행위.
        * **유가보조금 편취**: 화물차주 등과 공모하여 **허위 세금계산서**로 **가짜 주유 거래**를 꾸미고 정부 **유가보조금** 부정 수령.""",
        tactics=[
            EvasionTactic("유가보조금 부정수급 공모", "**화물차주**들과 짜고 **허위 세금계산서**(월 10억원) 발행, 실제 주유 없이 **유가보조금** 총 100억원 편취.", 100, [TaxType.VAT, TaxType.COMMON], MethodType.INTENTIONAL, AttackCategory.REVENUE), # 금액 상향
            EvasionTactic("자료상 행위 (중개)", "실물 거래 없이 **폭탄업체**로부터 **가짜 세금계산서**(50억원)를 매입하여 다른 법인에 수수료 받고 판매.", 50, TaxType.VAT, MethodType.INTENTIONAL, AttackCategory.COST) # 금액 상향
        ], defense_actions=["대표 명의 대포폰 사용 및 잠적.", "장부 허위 기장 및 파기.", "범죄 수익 해외 은닉 시도."]
    ),
     Company(
        name="㈜삼숭물산 (Samsoong)", size="대기업", revenue=60_000_000, operating_income=2_500_000, tax_target=1200, team_hp_damage=(20, 40),
        description="국내 굴지 **대기업 그룹**의 핵심 계열사. **경영권 승계**, **신사업 투자**, **해외 M&A** 활발.",
        real_case_desc="""[교육] 대기업 조사는 **그룹 전체**의 지배구조와 자금 흐름을 파악하는 것이 중요합니다. 주요 탈루 유형은 다음과 같습니다:
        * **일감 몰아주기/떼어주기**: 총수 일가 지분 높은 **계열사**에 **사업 기회** 제공, **통행세** 거래 등으로 부당 이익 제공 (**증여세**, **법인세** 문제).
        * **불공정 자본거래**: **합병, 분할, 증자** 등 자본거래 시 **가치 평가**를 왜곡하여 총수 일가 지분 가치 상승 (**증여세**, **법인세** 문제).
        * **해외 현지법인 이용**: **이전가격 조작**, **해외 배당금** 미신고, **국외 특수관계인**에게 자금 부당 지원 등 (**국제조세조정법**, **법인세** 문제).""",
        tactics=[
            EvasionTactic("일감 몰아주기 (통행세)", "**총수 자녀 회사**를 거래 중간에 끼워넣어 **통행세** 명목으로 연 500억원 부당 지원.", 500, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL),
            EvasionTactic("불공정 합병", "**총수 일가**에 유리하게 **계열사 합병 비율**을 산정하여 **이익** 200억원 증여.", 300, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL), # 금액 상향
            EvasionTactic("해외 현지법인 부당 지원", "**싱가포르 자회사**에 **업무 관련성** 없는 **컨설팅 수수료** 명목으로 400억원 부당 지급.", 400, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE)
        ], defense_actions=["대형 로펌 '**태평양**' 자문, '경영상 판단' 주장.", "공정위 등 타 부처 심의 결과 제시하며 반박.", "언론 통해 '**반기업 정서**' 프레임 활용.", "국회 통한 입법 로비 시도."]
    ),
    Company(
        name="구갈 코리아(유) (Googal)", size="외국계", revenue=3_000_000, operating_income=400_000, tax_target=1000, team_hp_damage=(18, 35), # 스탯 상향
        description="글로벌 **검색/플랫폼 기업** 한국 법인. **디지털 광고**, **클라우드** 사업 영위.",
        real_case_desc="""[교육] **디지털세** 논의를 촉발한 글로벌 IT 기업들은 **고정사업장** 개념 회피, **이전가격 조작** 등 지능적 조세회피 전략을 사용합니다:
        * **고정사업장 회피**: 국내 **서버** 운영, **국내 직원**이 핵심 계약 수행 등 실질적 사업 활동에도 불구, **단순 연락사무소** 또는 **자회사** 역할만 한다고 주장하여 **국내 원천소득** 과세 회피.
        * **이전가격(TP) 조작**: **아일랜드, 싱가포르** 등 **저세율국** 관계사에 **IP 사용료**, **경영지원 수수료** 등을 과다 지급하여 국내 소득 축소. **정상가격 산출 방법**의 적정성 여부가 핵심 쟁점.
        * **디지털 서비스 소득**: 국내 이용자 대상 **광고 수익**, **클라우드 서비스** 제공 대가 등의 **원천지** 규명 및 과세 문제.""",
        tactics=[
            EvasionTactic("이전가격(TP) 조작 - 경영지원료", "**싱가포르 지역본부**에 **실제 역할** 대비 과도한 **경영지원 수수료** 600억원 지급, 국내 이익 축소.", 600, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.CAPITAL), # 금액 상향
            EvasionTactic("고정사업장 회피", "국내 **클라우드 서버** 운영 및 **기술 지원** 인력이 **핵심적 역할** 수행함에도 **고정사업장** 미신고, 관련 소득 400억원 과세 회피.", 400, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.REVENUE) # 금액 상향
        ], defense_actions=["미국 본사 '**기술 이전 계약**' 근거 정상 거래 주장.", "**조세 조약** 및 **OECD 가이드라인** 해석 다툼 예고.", "**상호합의절차(MAP)** 신청 통한 시간 끌기 전략.", "각국 과세 당국 간 **정보 부족** 악용."]
    ),
    Company(
        name="(주)씨엔해운 (C&)", size="대기업", revenue=12_000_000, operating_income=600_000, tax_target=1600, team_hp_damage=(25, 45),
        description="글로벌 **컨테이너 선사**. **조세피난처 SPC** 활용 및 **선박금융** 관련 복잡한 거래 구조.",
        real_case_desc="""[교육] 해운업과 같이 **자본 집약적**이고 **국제적** 성격 강한 산업은 **조세피난처**를 이용한 탈세 유인이 큽니다:
        * **SPC 활용**: **파나마, 라이베리아, 마셜 군도** 등 선박 등록 편의 및 조세 혜택 주는 국가에 **서류상 회사(SPC)** 설립 후, **선박 소유권** 이전 및 **운항 소득** 귀속. SPC의 **실질 관리 장소**가 국내인지 여부가 쟁점.
        * **선박 금융**: 복잡한 **선박 금융 리스** 구조를 이용하여 **리스료** 지급 명목으로 국외 자금 유출 또는 **손실** 과다 계상.
        * **편의치적선**: 실제 선주국과 다른 국가에 선박 등록(**편의치적**)하여 **세금 회피** 및 **규제 완화** 혜택 누림.""",
        tactics=[
            EvasionTactic("역외탈세 (SPC 소득 은닉)", "**라이베리아** 등 **SPC** 명의 선박 **운항 소득** 1조 2천억원을 국내 미신고 및 해외 은닉.", 1000, TaxType.CORP, MethodType.CAPITAL_TX, AttackCategory.REVENUE), # 금액 조정
            EvasionTactic("선박 리스료 가장 지급", "**페이퍼컴퍼니**에 **선박 리스료** 명목으로 600억원 허위 지급 후 비자금 조성.", 600, TaxType.CORP, MethodType.INTENTIONAL, AttackCategory.CAPITAL)
        ], defense_actions=["해외 SPC는 '독립된 법인격' 주장.", "국제 해운 관행 및 현지 법률 준수 항변.", "**조세정보교환협정** 미체결국 이용, 자료 확보 방해.", "해운 불황으로 인한 '경영상 어려움' 호소."]
    ),
]

# --- 3. 게임 상태 초기화 및 관리 --- (이전과 동일)
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

# --- 4. 게임 로직 함수 --- (이전과 동일, SyntaxError 수정됨)

def start_player_turn():
    focus = sum(m.focus for m in st.session_state.player_team); st.session_state.player_focus_current=focus
    if "임향수" in [m.name for m in st.session_state.player_team]:
        st.session_state.player_focus_current+=1
        log_message("✨ [기획 조사] 집중력 +1!", "info")
    for art in st.session_state.player_artifacts:
        if art.effect["type"]=="on_turn_start" and art.effect["subtype"]=="focus":
            st.session_state.player_focus_current+=art.effect["value"]
            log_message(f"✨ {art.name} 집중력 +{art.effect['value']}!", "info")
    st.session_state.player_focus_max = st.session_state.player_focus_current
    if "김대지" in [m.name for m in st.session_state.player_team] and st.session_state.team_stats["data"]>=50 and not st.session_state.get('kim_dj_effect_used', False):
        new=copy.deepcopy(LOGIC_CARD_DB["b_tier_01"]); new.just_created=True; st.session_state.player_hand.append(new);
        log_message("✨ [부동산 조사] '금융거래 분석' 1장 획득!", "info"); st.session_state.kim_dj_effect_used=True
    st.session_state.cost_reduction_active = "전진" in [m.name for m in st.session_state.player_team];
    if st.session_state.cost_reduction_active:
        log_message("✨ [실무 지휘] 다음 카드 비용 -1!", "info")
    draw_n = 4 + st.session_state.get('bonus_draw', 0)
    if st.session_state.get('bonus_draw', 0)>0:
        log_message(f"✨ 조사계획서 효과로 카드 {st.session_state.bonus_draw}장 추가 드로우!", "info")
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

def execute_attack(card_index, tactic_index): # SyntaxError 수정됨, 로그 강화, 잔여 혐의 처리
    if card_index is None or card_index >= len(st.session_state.player_hand):
        st.toast("오류: 잘못된 카드 인덱스.", icon="🚨"); st.session_state.selected_card_index = None; st.rerun(); return
    card = st.session_state.player_hand[card_index]; cost = calculate_card_cost(card)
    company = st.session_state.current_battle_company
    is_residual = tactic_index >= len(company.tactics) # 잔여 혐의 여부
    tactic = ResidualTactic() if is_residual else company.tactics[tactic_index] # 잔여 또는 실제 혐의
    if st.session_state.player_focus_current < cost: st.toast(f"집중력 부족! ({cost})", icon="🧠"); st.session_state.selected_card_index = None; st.rerun(); return

    # --- 페널티 체크 (잔여 혐의는 통과) ---
    is_tax = is_residual or (TaxType.COMMON in card.tax_type) or (isinstance(tactic.tax_type, list) and any(tt in card.tax_type for tt in tactic.tax_type)) or (tactic.tax_type in card.tax_type)
    if not is_tax:
        t_types = [t.value for t in tactic.tax_type] if isinstance(tactic.tax_type, list) else [tactic.tax_type.value];
        log_message(f"❌ [세목 불일치!] '{card.name}' -> '{', '.join(t_types)}' (❤️-10)", "error"); st.session_state.team_hp -= 10;
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return
    is_cat = is_residual or (AttackCategory.COMMON in card.attack_category) or (tactic.tactic_category in card.attack_category)
    if not is_cat:
        log_message(f"🚨 [유형 불일치!] '{card.name}' -> '{tactic.tactic_category.value}' ({tactic.name}) (❤️-5)", "error"); st.session_state.team_hp -= 5;
        st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None; check_battle_end(); st.rerun(); return

    # --- 비용 지불 & 데미지 계산 (이전과 동일) ---
    st.session_state.player_focus_current -= cost;
    if st.session_state.get('turn_first_card_played', True): st.session_state.turn_first_card_played = False
    base = card.base_damage; ref = 500; scale = (company.tax_target / ref)**0.5 if company.tax_target > 0 else 0.5; capped = max(0.5, min(2.0, scale)); scaled = int(base * capped); scale_log = f" (규모 보정: {base}→{scaled})" if capped != 1.0 else ""; damage = scaled
    team_stats = st.session_state.team_stats; team_bonus = 0
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
    mult = 1.0; mult_log = ""
    # 잔여 혐의는 특수 효과 배율 없음
    if not is_residual and card.special_bonus and card.special_bonus.get('target_method') == tactic.method_type:
        m = card.special_bonus.get('multiplier', 1.0); mult *= m; mult_log += f"🔥[{card.special_bonus.get('bonus_desc')}] "
        if "조용규" in [m.name for m in st.session_state.player_team] and card.name == "판례 제시": mult *= 2; mult_log += "✨[세법 교본 x2] "
    if "한중히" in [m.name for m in st.session_state.player_team] and (company.size == "외국계" or tactic.method_type == MethodType.CAPITAL_TX): mult *= 1.3; mult_log += "✨[역외탈세 +30%] "
    if "서영택" in [m.name for m in st.session_state.player_team] and (company.size == "대기업" or company.size == "외국계") and TaxType.CORP in card.tax_type: mult *= 1.25; mult_log += "✨[대기업 +25%] "
    if "이현동" in [m.name for m in st.session_state.player_team] and tactic.method_type == MethodType.INTENTIONAL: mult *= 1.2; mult_log += "✨[지하경제 +20%] "
    final_dmg = int(damage * mult)

    # --- 오버킬 및 세액 계산 (잔여 혐의 분기) ---
    if is_residual:
        dmg_tactic = final_dmg; overkill = 0; overkill_contrib = 0
    else:
        remain = tactic.total_amount - tactic.exposed_amount; dmg_tactic = min(final_dmg, remain);
        overkill = final_dmg - dmg_tactic; overkill_contrib = int(overkill * 0.5);
        tactic.exposed_amount += dmg_tactic;
    company.current_collected_tax += (dmg_tactic + overkill_contrib)

    # --- 로그 강화 ---
    log_prefix = "▶️ [적중]" if mult <= 1.0 else ("💥 [치명타!]" if mult >= 2.0 else "👍 [효과적!]")
    target_name = tactic.name
    log_message(f"{log_prefix} '{card.name}' → '{target_name}'에 **{final_dmg}억원** 피해!{scale_log}", "success")
    if mult_log: log_message(f" ㄴ {mult_log}", "info")
    if not is_residual: # 잔여 혐의에는 카드/상황 로그 생략
        if card.name == "금융거래 분석": log_message(f"💬 금융 분석팀: 의심스러운 자금 흐름 포착!", "info")
        elif card.name == "차명계좌 추적": log_message(f"💬 조사팀: 은닉 계좌 추적 성공! 자금 흐름 확보!", "warning")
        elif card.name == "현장 압수수색": log_message(f"💬 현장팀: 압수수색으로 결정적 증거물 확보!", "warning")
        elif card.name == "자금출처조사": log_message(f"💬 조사팀: 자금 출처 소명 요구, 압박 수위 높임!", "info")
        elif tactic.method_type == MethodType.INTENTIONAL and final_dmg > tactic.total_amount * 0.5: log_message(f"💬 조사팀: 고의적 탈루 정황 가중! 추가 조사 필요.", "warning")
        elif tactic.method_type == MethodType.ERROR and '판례' in card.name: log_message(f"💬 법무팀: 유사 판례 제시하여 납세자 설득 중...", "info")
        elif tactic.method_type == MethodType.CAPITAL_TX: log_message(f"💬 분석팀: 복잡한 자본 거래 구조 분석 완료.", "info")
        if final_dmg < 10 and damage > 0: log_message(f"💬 조사관: 꼼꼼하게 증빙 대조하며 조금씩 밝혀냅니다.", "info")
        elif final_dmg > 100: log_message(f"💬 조사팀장: 결정적인 증거입니다! 큰 타격을 입혔습니다!", "success")

    if overkill > 0: log_message(f"📈 [초과 기여] 혐의 초과 데미지 {overkill}억 중 {overkill_contrib}억원을 추가 세액으로 확보!", "info")

    # --- 혐의 완료 처리 (잔여 혐의 제외, SyntaxError 수정됨) ---
    if not is_residual and tactic.exposed_amount >= tactic.total_amount and not getattr(tactic, '_logged_clear', False):
        setattr(tactic, 'is_cleared', True)
        setattr(tactic, '_logged_clear', True)
        log_message(f"🔥 [{tactic.name}] 혐의 완전 적발 완료! (총 {tactic.total_amount}억원)", "warning")
        if "벤츠" in card.text: log_message("💬 [현장] 법인소유 벤츠 키 확보!", "info")
        if "압수수색" in card.name: log_message("💬 [현장] 비밀장부 및 관련 증거물 다수 확보!", "info")

    st.session_state.player_discard.append(st.session_state.player_hand.pop(card_index)); st.session_state.selected_card_index = None;
    check_battle_end(); st.rerun()

# --- [수정됨] 자동 공격 로직 개선 ---
def execute_auto_attack():
    affordable_attacks = []
    # 1. 사용 가능한 공격 카드 필터링 및 정렬
    for i, card in enumerate(st.session_state.player_hand):
        if card.base_damage <= 0 or (card.special_effect and card.special_effect.get("type") in ["search_draw", "draw"]): continue
        cost = calculate_card_cost(card)
        if st.session_state.player_focus_current >= cost: affordable_attacks.append({'card': card, 'index': i, 'cost': cost})
    affordable_attacks.sort(key=lambda x: x['card'].base_damage, reverse=True) # 공격력 높은 순

    if not affordable_attacks:
        st.toast("⚡ 사용할 수 있는 자동 공격 카드가 없습니다.", icon="⚠️"); return

    # 2. 강한 카드부터 유효 타겟 검색 및 공격 시도
    company = st.session_state.current_battle_company; attack_executed = False
    all_tactics_cleared = all(t.is_cleared for t in company.tactics); target_not_met = company.current_collected_tax < company.tax_target

    for attack_info in affordable_attacks:
        current_card = attack_info['card']; current_idx = attack_info['index']; target_idx = -1
        # 실제 혐의 중 타겟 찾기
        if not all_tactics_cleared:
            for i, t in enumerate(company.tactics):
                if t.is_cleared: continue
                is_tax = (TaxType.COMMON in current_card.tax_type) or (isinstance(t.tax_type, list) and any(tt in current_card.tax_type for tt in t.tax_type)) or (t.tax_type in current_card.tax_type)
                is_cat = (AttackCategory.COMMON in current_card.attack_category) or (t.tactic_category in current_card.attack_category)
                if is_tax and is_cat: target_idx = i; break
        # 실제 혐의 없으면 잔여 혐의 타겟
        elif all_tactics_cleared and target_not_met: target_idx = len(company.tactics) # 가상 인덱스

        if target_idx != -1:
            target_name = "[잔여 혐의 조사]" if target_idx >= len(company.tactics) else company.tactics[target_idx].name
            log_message(f"⚡ 자동 공격: '{current_card.name}' -> '{target_name}'!", "info")
            execute_attack(current_idx, target_idx); attack_executed = True; break

    if not attack_executed: st.toast(f"⚡ 현재 손패의 카드로 공격 가능한 혐의가 없습니다.", icon="⚠️")

def end_player_turn():
    if 'kim_dj_effect_used' in st.session_state: st.session_state.kim_dj_effect_used = False
    if 'cost_reduction_active' in st.session_state: st.session_state.cost_reduction_active = False
    st.session_state.player_discard.extend(st.session_state.player_hand); st.session_state.player_hand = []; st.session_state.selected_card_index = None
    log_message("--- 기업 턴 시작 ---"); enemy_turn()
    if not check_battle_end():
        start_player_turn(); st.rerun() # 분리

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
        last_card_text = ""
        if st.session_state.player_discard: # IndexError 방지 강화
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
    # SyntaxError 수정됨
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

# --- 5. UI 화면 함수 ---

def show_main_menu(): # 이미지 URL 변경, 세미콜론 제거
    st.title("💼 세무조사: 덱빌딩 로그라이크"); st.markdown("---")
    st.header("국세청에 오신 것을 환영합니다.")
    st.markdown("당신은 오늘부로 세무조사팀에 발령받았습니다. 기업들의 교묘한 탈루 혐의를 밝혀내고, 공정한 과세를 실현하십시오.")
    st.image("https://www.nts.go.kr/nts/res/img/common/logo_nts.png", caption="국세청 CI", width=300)
    st.session_state.seed = st.number_input("RNG 시드 (0 = 랜덤)", value=0, step=1, help="동일 시드로 반복 테스트 가능")
    if st.button("🚨 조사 시작", type="primary", use_container_width=True):
        seed = st.session_state.get('seed', 0); random.seed(seed if seed != 0 else None)
        members = list(TAX_MAN_DB.values()); st.session_state.draft_team_choices = random.sample(members, min(len(members), 3))
        artifacts = list(ARTIFACT_DB.keys()); chosen_keys = random.sample(artifacts, min(len(artifacts), 3)); st.session_state.draft_artifact_choices = [ARTIFACT_DB[k] for k in chosen_keys]
        st.session_state.game_state = "GAME_SETUP_DRAFT"; st.rerun()
    with st.expander("📖 게임 방법", expanded=True): st.markdown("""**1.🎯 목표**: 기업 조사 → **'목표 추징 세액'** 달성 시 승리.\n**2.⚔️ 전투**: ❤️ **팀 체력**(0 시 패배), 🧠 **집중력**(카드 비용).\n**3.⚠️ 패널티**: **세목 불일치**(❤️-10), **유형 불일치**(❤️-5).\n**4.✨ 보너스**: 혐의 유형(`고의`, `오류`, `자본`) 맞는 카드 사용 시 추가 피해!""")

def show_setup_draft_screen():
    st.title("👨‍💼 조사팀 구성"); st.markdown("팀 **리더**와 시작 **조사도구** 선택:")
    if 'draft_team_choices' not in st.session_state or 'draft_artifact_choices' not in st.session_state:
        st.error("드래프트 정보 없음..."); st.button("메인 메뉴로", on_click=lambda: st.session_state.update(game_state="MAIN_MENU")); return
    teams = st.session_state.draft_team_choices; arts = st.session_state.draft_artifact_choices
    st.markdown("---"); st.subheader("1. 팀 리더 선택:"); lead_idx = st.radio("리더", range(len(teams)), format_func=lambda i: f"**{teams[i].name} ({teams[i].grade}급)** | {teams[i].description}\n   └ **{teams[i].ability_name}**: {teams[i].ability_desc}", label_visibility="collapsed")
    st.markdown("---"); st.subheader("2. 시작 조사도구 선택:"); art_idx = st.radio("도구", range(len(arts)), format_func=lambda i: f"**{arts[i].name}** | {arts[i].description}", label_visibility="collapsed")
    st.markdown("---");
    if st.button("이 구성으로 조사 시작", type="primary", use_container_width=True):
        initialize_game(teams[lead_idx], arts[art_idx])
        del st.session_state.draft_team_choices, st.session_state.draft_artifact_choices
        st.rerun()

def show_map_screen():
    if 'current_stage_level' not in st.session_state:
        st.warning("게임 상태 초기화됨..."); st.session_state.game_state = "MAIN_MENU"; st.rerun(); return
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

        all_tactics_cleared = all(getattr(t, 'is_cleared', False) for t in co.tactics) # getattr 추가
        target_not_met = co.current_collected_tax < co.tax_target

        tactic_cont = st.container(height=450)
        with tactic_cont:
            if all_tactics_cleared and target_not_met: # 잔여 혐의 표시
                res_t = ResidualTactic()
                with st.container(border=True):
                    st.markdown(f"**{res_t.name}** (`공통`, `단순 오류`, `공통`)"); st.markdown(f"*{res_t.description}*")
                    remain_tax = co.tax_target - co.current_collected_tax; st.progress(0.0, text=f"남은 추징 목표: {remain_tax:,}억원")
                    if is_sel:
                         card = st.session_state.player_hand[st.session_state.selected_card_index]
                         # 잔여 혐의 공격 버튼
                         if st.button(f"🎯 **{res_t.name}** 공격", key=f"attack_residual", use_container_width=True, type="primary"):
                             execute_attack(st.session_state.selected_card_index, len(co.tactics))
            elif not co.tactics and not target_not_met : st.write("(조사할 특정 혐의 없음)") # 목표 달성 시 메시지 추가
            else: # 기존 혐의 목록
                for i, t in enumerate(co.tactics):
                    cleared = getattr(t, 'is_cleared', False) # getattr 추가
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
    st.image("https://images.unsplash.com/photo-1543269865-cbf427effbad?q=80&w=1740&auto=format&fit=crop", caption="지친 조사관들...", width=400)
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
