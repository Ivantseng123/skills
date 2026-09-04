# 「不確定性宣告 + 交叉審查」手動審查工作流指南

本指南說明 `uncertainty-manifest` 與 `cross-review` 這兩個 skill 要怎麼手動搭配使用。兩者都由本 repo 提供,安裝方式見第 5 節。這裡沒有任何強制檢查機制——不會有東西在你動手改程式碼之前把你擋下來,每一步都是你自己判斷「現在該做這件事了」然後下指令。要說明的是:兩個 skill 的 description 仍然會讓代理自己主動觸發這套流程,沒有的是「機器強制擋下動作」那一層,不是模型的主動性。

## 1. 這套方法在解決什麼問題

LLM 沒有內建的「我不確定」訊號。產生文字的過程中,遇到自己其實在猜的地方,速度不會變慢、語氣不會改變——所以「不確定的時候要問」這種指令常常會悄悄失效,因為模型根本不會意識到自己正處於不確定狀態。

解法是反過來:不要期待模型「感覺到」不確定,而是強制它在動手改程式碼之前,先產出一份結構化、每一條都標明可信度的假設清單。這份清單就是 **Uncertainty Manifest(不確定性宣告)**。

有了這份清單,才有一個具體的東西可以拿去挑戰。**cross-review** 就是那個「拿新鮮眼光去挑戰」的審查程序:它刻意不看你原本的思考過程,只看宣告本身和程式碼/文件本身,逐條嘗試推翻。

兩者合起來可以理解成「合約與法庭」的設計:

- Manifest 是**合約**——把你隱藏的假設、未知項、跨來源衝突、領域名詞,全部攤在一份文件上。
- cross-review 是**法庭**——用一個獨立的子代理,依每條假設標的可信度分配查核火力,而不是每一行齊頭式地查一遍。

沒有 Manifest,cross-review 只能自己反推出一份隱含的假設清單再查(仍然有用,但比較貴、比較容易漏);沒有 cross-review,Manifest 就只是一份沒人挑戰過的自我感覺良好清單。

## 2. uncertainty-manifest:什麼時候手動調用、產出什麼

### 觸發時機

判斷基準是「計畫是否已經收斂成具體的檔案 / 方法 / schema 異動清單」——不是有沒有跑過正式的規劃流程。就算只是「幫我修個 bug」這種輕量任務,只要你心裡已經想好要改哪個檔案、改哪個方法,那一刻就該寫 Manifest。這其實是最常見的情況,不是例外。

唯一的例外是單行 typo 級、確定不涉及語意的修正:這種情況可以向使用者提出免寫 Manifest,由使用者裁決——代理不得自行豁免。

該手動觸發的時機:

- 計畫收斂成具體異動清單之後(包含輕量任務裡「隱含的計畫」)。
- 任何會動到 3 個以上檔案、或跨模組邊界的異動之前。
- 任何在受監管領域(保險、金融、醫療、法律等)的商業邏輯異動之前。
- 任何你即將講出一個沒有可引用來源的權威性主張時。

明確**不**觸發的情況:還在討論「方案 A 還是方案 B」的規格 / 設計階段。這個階段變更集還沒收斂,Manifest 無從錨定,先把討論收斂成具體的異動清單再回來寫。

### 產出結構

Manifest 有 4 個必要 section(§1–§4),每個至少要有 3 行實質內容——就算查完發現「什麼都沒有」,也要寫成 3 條「查了哪裡、沒發現什麼」的具體陳述,而不是留白。§1a / §1b 是掛在 §1 底下的**條件子節**:只有這次異動涉及欄位讀寫或跨 entity 參照時才必填;不適用時明寫「N/A — <一行理由>」即可,**不得灌三行水充數**——灌水只會騙到自己,還會讓下游審查把火力浪費在假條目上。

- **§1 Assumptions(假設)**:每條假設一句話陳述,附 `Source`(file:line / doc:section / 對話中的原話 / none)與 `Confidence` 標籤(見下)。`Source` 只能寫 `none` 時,`Confidence` 一定要標 `GUESS`,並把這條同時複製一份到 §2 Unknowns。
- **§1a Data Lineage(資料來源譜系)**:凡是這次異動會讀寫的每一個欄位都要有一條,寫明 `source_of_truth`(哪張表 / 哪個 entity 才是真正的來源)、`populated_by`(誰寫入)、`consumed_by`(誰讀取)、`alternative_sources_NOT_used`(同名但這次不採用的其他來源)、`why_not_alternative`(為什麼不用)。**只要同一個欄位名稱出現在 2 張以上的表,這條規則沒有例外,一定要寫**——這是為了抓「欄位名稱對、但讀錯表」這種在受監管領域代價最高的錯誤。若 `source_of_truth` 引不到真實的程式碼 / schema,這條就是 `Blocking`,要複製到 §2。
- **§1b Cardinality(基數)**:凡是跨 entity 的參照關係都要有一條,寫明 `cardinality`(1:1 / 1:N / N:M)、`evidence`、`user_confirmed`(yes / no / not_yet)、`implementation_depends_on_cardinality`(yes / no)。若 `user_confirmed: not_yet` 且 `implementation_depends_on_cardinality: yes`,這條就是 `Blocking`,要複製到 §2,並且**先問過人再繼續寫程式碼**。基數是商業事實,不是能從程式碼猜出來的東西——例如一個回傳單一結果的查詢方法,也可能只是「一堆裡面挑第一筆」,不代表關係真的是 1:1。
- **§2 Unknowns(未知項)**:每條都要附一個封閉式的釐清問題(能用 yes/no 或選擇題回答,不要開放式問題),以及 `Blocking: yes/no`。`Blocking: yes` 的項目必須在動手實作前解決;`Blocking: no` 可以先擱著之後再處理。
- **§3 Cross-source conflicts(跨來源衝突)**:至少列 3 個「有實際去查過」的檢查點,每條寫 Source A 說了什麼、Source B 說了什麼、`Resolution`(哪個為準,或 `PENDING`)。「沒有衝突」是合法結論,但前提是真的查過——省略不等於確認過沒有衝突。
- **§4 Domain terms(領域名詞)**:列出這次異動用到的每個領域專有名詞,標明它在哪份 glossary / 文件有定義,或標 `NEW_TERM`。標 `NEW_TERM` 的名詞要停下來問人,**不能自己從上下文腦補意思**——這正是「似是而非的錯誤術語」溜進受監管領域程式碼的典型路徑。

### Confidence 標籤

每條 §1 假設一定要標,沒標的一律當 `INFERRED` 處理。兩個標籤之間猶豫不決時,一律取比較低的那個。

| 標籤 | 定義 |
|---|---|
| `VERIFIED` | 這個 session 裡**真的執行過**(跑了測試 / 查詢 / 指令)並親眼看到結果,而且執行的必須是主張本身(例如跑那個能證明行為的測試、跑那條查詢看到宣稱的值)——單純 grep / Read / ls 只能證明「這段文字存在」,頂多算 `CITED`。 |
| `CITED` | 有具體來源可引用(file:line / 官方文件 / 使用者原話),但沒有實際執行過。 |
| `INFERRED` | 從讀程式碼、命名慣例、慣例推論出來,主張本身沒有直接來源可引。 |
| `GUESS` | 沒有誠實的來源可引。`GUESS` 不丟臉,標出來就是它的用途——把這個項目導向使用者裁決,而不是悄悄當真的用下去。 |

### 規模自判(S / M / L)

每次寫 Manifest 前,先自己判斷這次異動屬於哪一級——沒有工具會替你判斷,判斷錯了也沒有東西會糾正你:

- **S 級**:≤2 個檔案、≤20 行、不涉及商業邏輯。商業邏輯的定義是:會影響金額 / 費率 / 分攤計算、狀態轉換、或對外可見行為的程式碼——**無法確定屬於哪一類時,一律當 M 級處理**。S 級仍要寫完整 4 個 section,§3 仍要有 ≥3 次真的執行過的查核,但可以跳過第 3 節會講的 `cross-review plan` 這一步。
- **M 級**:3–10 個檔案,或任何商業邏輯 / 跨模組異動。完整 Manifest,且要跑一次 `cross-review plan`(諮詢性質,但每個 Critical 都要一項一項回報處理,見第 3 節)。
- **L 級**:>10 個檔案、涉及 schema、或跨系統異動。做法同 M 級,外加:分批實作,每一批結束時都要能獨立驗證通過。

### 檔案落點

Manifest 存在 `<專案根目錄>/docs/manifest/<task-slug>.md`,`task-slug` 是自己取的簡短 kebab-case 名稱(例如 `fix-discount-rate`)。同一個任務永遠對應同一個檔案,後續更新是覆寫這個檔案,不是另外開一份。這個路徑刻意不綁定任何 agent:Manifest 是規劃、實作、審查共用的任務產物,不是 agent 設定,所以不放在 `.claude/`、`.codex/` 之類的工具專屬目錄。要不要把 `docs/manifest/` 進版控由各 repo 自己決定,skill 不會動你的 `.gitignore`。你也可以在檔案開頭的 YAML frontmatter 加一個 `file_globs` 欄位,列出這次異動預期會碰到的檔案路徑——這在沒有機器強制檢查的情況下,單純是給自己(或協作者)看的範圍聲明,寫了對追蹤「這份 Manifest 對應到哪些檔案」還是有幫助。

## 3. cross-review:各層級什麼時候手動調用、審查火力怎麼分配

### 三種層級

| 指令 | 時機 | 政策 |
|---|---|---|
| `cross-review spec` | 規格草稿寫完後 | 諮詢性質 |
| `cross-review plan` | Manifest 寫完或更新後(S 級可跳過) | 諮詢性質,但 Critical 必須逐項處理 |
| `cross-review pr` | 準備 `git push` / 開 PR 之前 | 有 Critical 就阻斷,不能推 |

「因應審查報告而更新 Manifest」本身不會重新觸發 `plan` 級審查——不然會變成無窮迴圈。只有當更新新增了 ≥2 個新的 `GUESS`,或 ≥1 個新的 `Blocking: yes` Unknown,才需要重跑一次 `plan` 級審查;最多自動重跑 2 次,第 3 次起要先明確問過使用者才能再跑。

### 兩種審查模式

- **Anchored(有 Manifest 時優先採用)**:審查者逐行走過 Manifest §1–§4,獨立驗證每個引用來源,挑戰已經被寫出來的假設。ROI 最高,因為作者已經先做了「試圖攤開隱藏假設」這件事,審查者只需要去驗證。
- **Open(沒有 Manifest 時的退路)**:常見於審查別人寫的 PR、legacy 程式碼、第三方 patch,或是你自己跳過了寫 Manifest 這一步。審查者會自己先從被審物件反推出一份隱含的假設清單,再挑戰它。一樣有用,但比 anchored 貴、也比較容易漏——能寫 Manifest 時優先寫。

### 審查火力如何依 Confidence 標籤分配

這是整個機制存在的理由:把查核力氣集中在真正不確定的地方,而不是每一行齊頭式地查。

- `VERIFIED` → 跳過,除非有別的發現跟它矛盾。
- `CITED` → 抽查至少 3 條(不到 3 條就全查)。
- `INFERRED` → 每一條都要嘗試**推翻**(grep、實際執行、找第二個來源)。
- `GUESS` → 同樣逐條嘗試推翻,而且不論推翻結果如何,都要在報告中標成「需要使用者裁決」。
- 沒標 Confidence 的 §1 項目一律當 `INFERRED` 處理;§1a / §1b 的項目本來就不帶 Confidence 標籤(這不算一個發現),同樣當 `INFERRED` 處理。

### 怎麼實際執行審查

**一定要開一個獨立的子代理**去做審查——這個子代理看不到你原本的思考過程,這正是它的價值所在。絕對不要自己在同一個對話裡邊 grep 邊寫評語然後說這是 cross-review:那不是新鮮眼光,是自我背書,只會給人一種「審查過了」的假安全感,比完全不審查更糟。

給審查子代理的輸入固定包含 4 樣:

1. 被審物件本身(spec / plan 全文,或 `git diff <base>...HEAD` 的輸出加上 PR 標題與描述)。
2. 完整的 Manifest 內容(§1–§4,anchored 模式才有,open 模式不附)。
3. 執行環境資訊(工作目錄、程式碼庫根目錄、相關路徑)。
4. 模式標記(`Anchored` 或 `Open`),讓子代理知道自己第一步該怎麼切入。

絕對不要把你自己原本的推理過程餵給審查子代理——那樣審查會繼承你的偏見,變成確認式審查而不是挑戰式審查。

spec / plan 層級開一個子代理即可。PR 層級要開一個由 3 個角度不同的子代理組成的小組,平行執行(見下)。

### PR 審查的三面鏡設計

`cross-review pr` 平行開 3 個獨立子代理,各自拿到同一份 diff + 同一份 Manifest,但任務不同:

1. **正確性鏡**:一般程式碼正確性審查(邊界條件、bug、依上面 Confidence 分配去驗證假設)。
2. **機敏資料 / 範圍鏡**:專門檢查 diff 有沒有洩漏機密 / 個資 / 內部識別碼,以及有沒有偷渡超出範圍的異動、注入或授權風險。這面鏡子不看 Confidence 標籤,Manifest 只是背景資料,不是它的檢核清單。
3. **領域鏡**:檢查 diff 有沒有用錯領域名詞、業務邏輯是否跟 Manifest §1 / §1a / §1b 的主張矛盾。同樣不看 Confidence 標籤。

三面鏡預設全部都用 `general-purpose` 子代理型別,把上面的任務描述連同輸出格式一起寫進 prompt 就成立——不需要額外安裝任何專用審查代理。你的環境若剛好有專門的 code reviewer / security auditor 代理型別,可以把前兩面鏡換成它們,任務描述照抄不變。

只有當 diff 小於 50 行、且不涉及 schema、不涉及領域名詞時,才可以退到 2 面鏡子(拿掉領域鏡)——正確性鏡與機敏資料鏡永遠不能拿掉。3 份報告由你自己合併:同一個發現取最高嚴重度;兩面鏡子對同一項有分歧時,講得出具體失敗場景的那個為準。

### Critical 判準

一個 🔴 Critical 如果講不出「什麼輸入 / 狀態 → 造成什麼具體錯誤結果」這個具體失敗場景,就要自動降級成 🟡 Major,不能只憑感覺喊 Critical。這條規則是為了防止「幻覺出一個 Critical → 修 → 重跑 → 又幻覺一個新的」這種無窮迴圈。

### PR 阻斷流程(有 Critical 時)

1. 發現有 🔴 Critical → **停下來**,不要 `git push` / 開 PR。
2. 一項一項裁決每個 Critical:吸收修正 / 反駁 / 延後處理,並寫下理由。
3. 依吸收的 Critical 修改程式碼。
4. 同步更新 Manifest §1–§4,讓它符合即將 push 的 diff——Manifest 跟實際 diff 對不上,這件事本身就算一個 Critical。
5. 重跑一次 `cross-review pr`(新的 diff + 新的 Manifest)。
6. 迴圈直到報告裡 0 個 🔴 Critical。最多自動重跑 2 次,第 3 次起要先明確拿到「可以再跑」的同意才能繼續。
7. 確認 0 個 Critical 之後才能真的 `git push` / 開 PR。

使用者(或你自己審慎決定後)可以明確覆寫某個 Critical(例如「這個我知道,還是要 merge」),但覆寫要寫進 PR 描述裡一個「已知悉但未解決的 Critical」清單,附上理由——覆寫必須是一個明確、寫下來的決定,不能悄悄放行。

### spec / plan 層級的 Critical 一樣不能已讀不回

雖然 spec / plan 是諮詢性質,不會機械式阻擋你繼續,但只要報告裡出現 🔴 Critical,還是要:先更新 Manifest 吸收或反駁這個發現,然後把每個 Critical 逐項回報決定(吸收 / 反駁 / 延後)和理由,等到這個決定確定下來才繼續往下寫程式碼。「諮詢性質」指的是流程不會自動擋,不是說可以默默略過。

## 4. 建議的手動工作流

1. 計畫收斂成具體的檔案 / 方法 / schema 異動清單 → 寫(或更新)Manifest。
2. 手動呼叫 `cross-review plan`(S 級可跳過)。有 Critical → 依第 3 節「spec / plan 層級」的規則處理完才繼續。
3. 動手實作,照 Manifest 的假設走;過程中若發現某個假設其實錯了,回頭更新 Manifest。
4. 準備 push / 開 PR 之前,手動呼叫 `cross-review pr`。有 Critical → 走第 3 節的阻斷流程,直到 0 個 Critical 才真的推。

以下檢查沒有任何機制代勞,全部靠你自己執行:

- Manifest 是否真的存在,4 個必要 section 是否都有 ≥3 行實質內容(§1a / §1b 不適用時寫「N/A — 理由」,不灌水)——沒有東西會擋你亂寫 3 行湊數,誠實與否只能靠自己。
- Manifest 是否夠新鮮——可檢查的判準是「工作目錄有沒有發生 Manifest 沒預期到的變動」:別人的 commit 進來了、pull/rebase 改寫了檔案、或你自己的修改跑出了它宣告的範圍,都算過期;你自己計畫內、範圍內的編輯本來就是它預期的事,不算。過期就在下一次動手改程式碼之前重讀一遍、確認假設還成立並就地更新,不要拿一份過時的假設清單去跑 `cross-review pr`。
- Manifest 宣告的範圍是否真的涵蓋你正在改的檔案——沒有東西會擋你「拿 A 任務的 Manifest 去合理化 B 任務的異動」,這件事現在要靠自己盯著。
- 遇到 `GUESS` 或 `Blocking: yes` 的項目時,「先問人、同一輪不能繼續做」這件事完全靠自律。
- Critical 阻斷 push 這件事,現在只是一條規則,不是機制——沒有東西會真的擋住你按下 `git push`,自己要做到說到做到。

## 5. 安裝與相依

兩個 skill 都由本 repo 提供,整個 repo 就是一個名為 `skills` 的 plugin,裝一次即可(連同 repo 內其他 skill 一起)。

**Claude Code plugin:**

```bash
/plugin marketplace add Ivantseng123/skills
/plugin install skills@ivantseng123-skills
```

**Codex plugin**(Codex App,或較新版的 codex CLI):

```bash
codex plugin marketplace add Ivantseng123/skills
codex plugin add skills@ivantseng123-skills
```

裝完之後重啟 Codex(或開一個新的 thread)。

**OpenCode / Cursor / Copilot 等其他代理**——用跨代理的 [`skills`](https://skills.sh) CLI,它直接讀這個公開 repo,不需要註冊 marketplace:

```bash
npx skills add Ivantseng123/skills -a opencode   # OpenCode
npx skills add Ivantseng123/skills -a cursor     # Cursor(或 -a windsurf、-a cline…)
npx skills add Ivantseng123/skills -g            # 所有偵測到的代理,全域安裝
```

只想裝這兩個 skill、不要 repo 內其他 skill 的話,加 `--skill`:

```bash
npx skills add Ivantseng123/skills --skill uncertainty-manifest -g
npx skills add Ivantseng123/skills --skill cross-review -g
```

**退路(不想用任何安裝工具時)**:直接把本 repo 的 `skills/uncertainty-manifest/` 與 `skills/cross-review/` 兩個資料夾複製到 `~/.claude/skills/` 底下,Claude Code 一樣認得,可以用 `/uncertainty-manifest`、`/cross-review` 之類的方式手動呼叫(實際呼叫語法依你的版本而定)。

兩份 SKILL.md 裡實際引用到的外部項目,以及每一項「需不需要、沒有的話怎麼辦」:

| 引用項目 | 需要嗎 | 沒有的話怎麼辦 |
|---|---|---|
| `general-purpose` 子代理型別(spec/plan 審查的預設審查者、PR 層級三面鏡的預設型別都用它) | 需要 | Claude Code 內建;Codex 用它的子任務委派機制;其他代理請先確認能不能 spawn 隔離子代理,不能的話 → 依 cross-review SKILL.md 的規則明講 skip,絕不做同 context 的假審查 |
| 開獨立子代理的機制(Task / Agent 之類的工具) | 需要 | 這是整個 cross-review 機制的前提;若當下環境真的開不了獨立子代理,要明講「這個環境開不了獨立審查」,不能假裝審查過 |
| 專用的 code reviewer 子代理型別(PR 正確性鏡) | 非必要 | 預設就是 `general-purpose` 加上第 3 節「三面鏡」的正確性任務描述與輸出格式(逐項評估 / 隱藏衝突 / 事前驗屍 / 嚴重度分級),效果等價;環境剛好有專用型別時換上去即可 |
| 專用的 security auditor 子代理型別(PR 機敏資料/範圍鏡) | 非必要 | 同上,預設 `general-purpose`,任務描述改成機敏資料 / 範圍檢查 |
| `Explore` 這類「只讀片段、不讀全文」的搜尋型子代理 | 不要用 | 明確避免拿這種型別做審查——審查需要讀全文,片段式閱讀會漏掉東西,而且它會很有自信地把「沒打開過」講成「找不到」 |
| 規格階段發散討論的相關工具或流程 | 非必要 | 沒有專門工具時,規格還在收斂、方案 A/B 還沒定案的階段,用一般對話討論即可,等收斂成具體異動清單再回來寫 Manifest |
| Manifest 存在性 / 完整性 / 新鮮度 / 範圍的強制檢查機制 | 沒有 | 這些檢查全部是第 6 節列出的手動紀律項目,SKILL.md 內也把它們寫成明文規則 |
| 繞道寫檔的偵測機制 | 沒有 | 同上,是手動紀律——任何繞過正式編輯工具的寫入一律視為違反紀律 |
| S / M / L 規模定義 | 需要,但已內化 | 本指南第 2 節與 `uncertainty-manifest` 的 SKILL.md 都已寫入定義,不需要另外找別的文件 |

## 6. 沒有強制檢查機制,哪些事要靠自己守住

這兩個 skill 是純文字規則,不附帶任何會在你寫 / 改程式碼檔案之前自動擋下來的檢查機制。以下這些檢查點,全部由你自己負責:

- **存在性**:Manifest 檔案根本不存在,卻已經直接動手改程式碼。
- **完整性**:Manifest 存在,但 4 個必要 section 沒有寫滿(每個至少 3 行實質內容;§1a / §1b 不適用時應明寫「N/A — 理由」,不得留白或灌水),或某個 section 根本是空的。
- **新鮮度**:工作目錄發生了 Manifest 沒預期到的變動(別人的 commit、pull/rebase、超出宣告範圍的修改),你卻還拿這份過時的假設清單去改今天的程式碼。
- **範圍一致性**:Manifest 宣告的檔案範圍跟你實際在改的檔案對不上——例如拿舊任務的 Manifest 去正當化新任務的異動。
- **繞道寫檔**:任何繞過正式編輯工具的寫入(shell 重導、heredoc、腳本代寫)一律視為違反紀律,無論技術上可不可行。
- **typo 級豁免**:單行 typo 級的修正可以向使用者提出免寫 Manifest,由使用者裁決;代理不得自行豁免——這條沒有東西會替你把關。

除了「檔案本身合不合格」以外,工作流層面還有兩個**觸發點**,一樣要靠自己執行(skill 的 description 會讓代理主動想起來,但沒有任何機制強制它發生):

- 寫完 / 更新 Manifest 後,接著跑一次 `cross-review plan`。
- 準備 `git push` / 開 PR 前,跑一次 `cross-review pr`。

以及最後一道:**PR 有 Critical 時「不准 push」這件事,是紙上的規則,不是機制**——沒有任何東西會真的擋住你按下 `git push`,能不能做到完全取決於你自己的紀律。
