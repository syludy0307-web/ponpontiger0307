/* ===========================================================
   slides.js — スライド本文データ
   -----------------------------------------------------------
   情報の扱い方（重要）
     tag: confirmed … 報道・公式発表で確認されている事項
     tag: unknown   … まだ判明していない／確認前の事項
     tag: hypo      … 仮説・可能性の列挙
     tag: knowledge … 今回の取材情報ではなく、教科書的な一般知識
                      （ガスの性質、法令の枠組み、調査手順など）

   このデッキは「わかっていないことを、わかっていないまま示す」ための
   構成になっている。一般知識(knowledge)を足すことはあっても、
   今回の事故についての新しい事実を推測で書き足してはいけない。

   写真について
     この事故当日の報道写真はパブリックライセンスで入手できないため、
     ここに載せているのはすべて
       site … 当該施設の「平時」の写真
       ref  … 別の災害・別の事故の参考写真
     である。実写を差し込む場合は slot ブロックの手順に従う。
   =========================================================== */
(function (global) {
  'use strict';

  var UP = 'https://upload.wikimedia.org/wikipedia/commons/';

  /* --- 写真プール（すべて Wikimedia Commons / URL 実在確認済み） --- */
  var P = {
    mall1: { src: UP + '3/38/AEON_MALL_Kumamoto_Clair_202204.jpg',
      kind: 'site', badge: '当該施設・平時',
      title: 'イオンモール熊本（2022年）',
      credit: 'Wikimedia Commons / CC BY-SA' },
    mall2: { src: UP + 'd/d4/Aeonmall_Kumamoto_Panorama.JPG',
      kind: 'site', badge: '当該施設・平時',
      title: 'イオンモール熊本 全景',
      credit: 'Wikimedia Commons / CC BY-SA' },
    odaiba: { src: UP + 'f/fe/Odaiba_fire_as_seen_from_Marunouch_area_during_8.9mb_earthquake.jpg',
      kind: 'ref', badge: '参考写真・別災害',
      title: '地震時に発生した火災（2011年・お台場）',
      credit: 'Wikimedia Commons' },
    noto: { src: UP + 'c/cb/JSDF_Noto_Earthquake_2024-01-10_6_%28Search_and_Rescue%29.jpg',
      kind: 'ref', badge: '参考写真・別災害',
      title: '能登半島地震での捜索救助（2024年・自衛隊）',
      credit: '防衛省 / Wikimedia Commons' },
    gasexp: { src: UP + '6/61/Building_destroyed_by_gas_explosion_-_geograph.org.uk_-_1731825.jpg',
      kind: 'ref', badge: '参考写真・別事案',
      title: 'ガス爆発で破壊された建物（英国）',
      credit: 'geograph.org.uk / CC BY-SA' },
    kumamoto2016: { src: UP + '5/5e/Destroyed_house_by_2016_Kumamoto_earthquake.jpg',
      kind: 'ref', badge: '参考写真・2016年',
      title: '2016年熊本地震の被害',
      credit: 'Wikimedia Commons' },
    castle: { src: UP + '0/00/2016_Kumamoto_earthquake_Kumamoto_Castle_1.JPG',
      kind: 'ref', badge: '参考写真・2016年',
      title: '2016年熊本地震で被災した熊本城',
      credit: 'Wikimedia Commons / CC BY-SA 3.0' },
    aso: { src: UP + '7/73/Aso_house_damaged_by_the_2016_Kumamoto_earthquake_2.jpg',
      kind: 'ref', badge: '参考写真・2016年',
      title: '2016年熊本地震で損壊した家屋（阿蘇）',
      credit: 'Wikimedia Commons / CC BY-SA 3.0' },
    meter1: { src: UP + '4/48/Mycon_gas_mater.jpg',
      kind: 'ref', badge: '参考写真・一般例',
      title: 'マイコンメーター（感震遮断機能つきガスメーター）',
      credit: 'Wikimedia Commons / CC BY-SA 3.0' },
    meter2: { src: UP + 'b/b0/Yazaki_Microcomputer_Gas_Meter_SY25MT1e_20170405.jpg',
      kind: 'ref', badge: '参考写真・一般例',
      title: 'マイコンメーターの表示部',
      credit: 'Wikimedia Commons / CC BY-SA 4.0' },
    magnitogorsk: { src: UP + '4/46/%D0%9F%D0%BE%D1%81%D0%BB%D0%B5%D0%B4%D1%81%D1%82%D0%B2%D0%B8%D1%8F_%D0%B2%D0%B7%D1%80%D1%8B%D0%B2%D0%B0_%D0%B8_%D1%80%D0%B0%D0%B7%D1%80%D1%83%D1%88%D0%B5%D0%BD%D0%B8%D1%8F_%D0%B4%D0%BE%D0%BC%D0%B0_%D0%B2_%D0%9C%D0%B0%D0%B3%D0%BD%D0%B8%D1%82%D0%BE%D0%B3%D0%BE%D1%80%D1%81%D0%BA%D0%B5.png',
      kind: 'ref', badge: '参考写真・別事案',
      title: 'ガス爆発による集合住宅の崩落（2018年・マグニトゴルスク）',
      credit: 'Wikimedia Commons / CC BY 4.0' },
    firedoor: { src: UP + '1/1e/Kushida_Shrine_Station_Bicycle_Parking_the_fire_door_Fukuoka_20231215.jpg',
      kind: 'ref', badge: '参考写真・一般例',
      title: '防火扉（一般的な例）',
      credit: 'Wikimedia Commons / CC BY-SA 4.0' },
    ukisar: { src: UP + '8/8b/UKISAR_in_2011_Japan_earthquake_12_UK_rescuers_carry_out_searches_in_Unosumia.jpg',
      kind: 'ref', badge: '参考写真・別災害',
      title: '被災地での捜索活動（2011年）',
      credit: 'Wikimedia Commons / CC BY 2.0' }
  };

  /* 実写差し替えスロット（報道写真などを自分で用意して差し込む場所） */
  function slot(what, file) {
    return { t: 'slot', what: what, file: file };
  }

  var SLIDES = [

    /* 01 ------------------------------------------------------------- */
    {
      kicker: '令和8年熊本地震｜2026.07.28',
      title: '地震の約1時間半後<br><span class="hl-red">モールで大爆発</span>',
      lead: 'しかし、爆発の全容はまだ見えていない。何が起き、何が判明していないのか。',
      bg: P.mall1.src,
      layout: 'full',
      ambient: 'blast',
      body: [
        { t: 'facts', items: [
          { v: 'M7.1', l: '地震の規模' },
          { v: '震度7', l: '最大震度' },
          { v: '約80〜90分', l: '地震から爆発までの時間差' },
          { v: '20', l: 'このデッキで扱う論点' }
        ] },
        { t: 'note', html: 'このデッキは<b>「確定していること」と「まだ判明していないこと」を混ぜない</b>ことを唯一のルールにしている。色のついたタグが、その情報の確度を示す。' }
      ],
      source: '背景：イオンモール熊本の平時写真（Wikimedia Commons）／事件写真ではありません',
      image: {
        kicker: 'イメージ 01',
        title: '爆発の広がり方（概念図）',
        scene: 'blast',
        caption: '爆発の起点・規模・破片の飛散範囲はいずれも未公表。図は現象の説明のためのイメージであり、実際の配置ではない。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            'ガス爆発は「爆発点」から球状に圧力が広がる',
            '圧力は弱い面（外壁・開口部）へ抜ける',
            '飛散物は爆発そのものより広範囲に届くことがある'
          ], cls: 'small' },
          { t: 'photo', p: P.mall2 }
        ]
      }
    },

    /* 02 ------------------------------------------------------------- */
    {
      kicker: 'まず結論',
      title: '“ガス漏れ”は有力。<br>だが、原因確定ではない',
      bg: P.mall2.src,
      layout: 'split',
      ambient: 'gasleak',
      left: [
        { t: 'panel', tags: [['confirmed', '確認報道'], ['unknown', '未確定']], items: [
          '政府関係者から「ガス漏れ」との報告',
          '現場でガス臭を感じたとの証言',
          'ただし漏出箇所・着火源・設備作動状況は未判明'
        ] },
        { t: 'note', html: '「有力」と「確定」は違う。原因の確定は、消防・警察の実況見分と鑑定を経てから出る。' }
      ],
      right: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          'ガス爆発と判断するには、漏出源・可燃濃度・着火源の3点が要る',
          '「ガス臭がした」だけでは、漏出源の特定にはならない',
          '原因調査の結論は数週間〜数か月かかることが多い'
        ], cls: 'small' }
      ],
      source: '出典：毎日新聞、テレビ朝日など（2026年7月29日時点）',
      image: {
        kicker: 'イメージ 02',
        title: 'ガスはどう漏れて、どう溜まるか',
        scene: 'gasleak',
        caption: '配管の破断部からガスが漏れ、換気の弱い場所に溜まっていく——という一般的な経過のイメージ。今回の漏出箇所は未公表。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            'LPガス（プロパン）は空気より<b>重い</b>ため、床面・地下・ピットに溜まる',
            '都市ガス13A（メタン主体）は空気より<b>軽い</b>ため、天井付近に溜まる',
            'どちらに該当するかで、溜まる場所も探し方も変わる'
          ], cls: 'small' },
          { t: 'facts', items: [
            { v: '2.1〜9.5%', l: 'プロパンが燃える濃度範囲' },
            { v: '5〜15%', l: 'メタンが燃える濃度範囲' }
          ] },
          { t: 'note', html: '濃すぎても薄すぎても燃えない。<b>この範囲に入った瞬間</b>だけが危険になる。' }
        ]
      }
    },

    /* 03 ------------------------------------------------------------- */
    {
      kicker: '地震の概要',
      title: '最大震度7',
      layout: 'split',
      ambient: 'quake',
      left: [
        { t: 'html', html: '<div class="big-number">M7.1</div>' },
        { t: 'html', html: '<p class="lead" style="max-width:100%">7月28日16時27分、熊本県熊本地方。深さ16km、横ずれ断層型。</p>' },
        { t: 'facts', items: [
          { v: '16km', l: '震源の深さ' },
          { v: '階級4', l: '長周期地震動階級（最大が4）' },
          { v: '16:27', l: '発生時刻' }
        ] }
      ],
      right: [
        { t: 'panel', tags: [['confirmed', '気象庁発表']], items: [
          '宇城市・氷川町で震度7',
          '長周期地震動階級4',
          '気象庁が「令和8年熊本地震」と命名'
        ] },
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          '震度7は震度階級の最上位で、上限がない',
          '長周期地震動階級4は最上位。高層階が大きく長く揺れる',
          '横ずれ断層型＝断層が水平方向にずれるタイプ'
        ], cls: 'tiny' }
      ],
      source: '出典：気象庁「令和8年熊本地震について（第3報）」',
      image: {
        kicker: 'イメージ 03',
        title: '揺れはどう伝わったか',
        scene: 'quake',
        caption: '震源から地表へ、揺れが同心円状に広がるイメージ。実際の震度分布は気象庁の発表を参照。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            'マグニチュード＝地震そのものの大きさ',
            '震度＝その場所での揺れの強さ。同じ地震でも場所で変わる',
            '深さ16kmは「浅い」地震で、直上の揺れが強くなりやすい'
          ], cls: 'small' },
          { t: 'photo', p: P.castle }
        ]
      }
    },

    /* 04 ------------------------------------------------------------- */
    {
      kicker: '時間差の謎',
      title: '地震直後ではなく、<span class="hl-amber">約80〜90分後</span>',
      layout: 'full',
      ambient: 'clock',
      guardBottom: true,
      body: [
        { t: 'timeline', items: [
          { b: '16:27', s: 'M7.1の地震発生' },
          { b: '直後', s: '客を中心に避難開始' },
          { b: '17:45頃', s: '大きな爆発音との証言' },
          { b: '18:00頃', s: '白煙・爆発の119番通報' }
        ] },
        { t: 'warning', html: '時間差は「漏れたガスが徐々に蓄積した」説明と整合する。ただし、それを裏づける公式鑑定はまだない。' },
        { t: 'note', html: '<b>一般知識：</b>漏れる速度が小さいほど、可燃濃度に達するまで時間がかかる。逆に言えば、<b>時間差の長さは漏出量の手がかり</b>になりうる——鑑定が出れば。' }
      ],
      source: '時刻は初期報道に幅あり。今後、消防・警察の時系列で更新される可能性があります。',
      image: {
        kicker: 'イメージ 04',
        title: 'なぜ、すぐに爆発しなかったのか',
        scene: 'clock',
        caption: '時間が経つほどガスが溜まり、やがて燃える濃度に入る——という蓄積のイメージ。',
        side: [
          { t: 'panel', tags: [['hypo', '仮説']], items: [
            '漏出量が少なく、濃度上昇に時間がかかった',
            '避難で人が減り、扉が閉まって換気が落ちた',
            '停電・復電のタイミングが着火に関わった'
          ], cls: 'small' },
          { t: 'panel', tags: [['unknown', '未判明']], items: [
            '実際の漏出開始時刻',
            '爆発時点での濃度・範囲'
          ], cls: 'small' }
        ]
      }
    },

    /* 05 ------------------------------------------------------------- */
    {
      kicker: '不明点 01',
      title: 'ガスは<br>どこから漏れた？',
      layout: 'split',
      ambient: 'pipes',
      left: [
        { t: 'list', items: [
          'LPガス貯蔵設備',
          '建物へ入る主管',
          '飲食店の個別配管',
          '厨房機器との接続部'
        ] },
        { t: 'note', html: '大型商業施設は、1本の配管ではなく<b>枝分かれした網</b>でガスを配る。破断が1か所とは限らない。' }
      ],
      right: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          '地震で壊れやすいのは、硬い配管どうしの<b>継手</b>と、機器との<b>接続部</b>',
          '天井裏や壁内の配管は、外から見えないため発見が遅れる',
          '建物が傾くと、配管は引っぱられて抜ける方向に壊れる'
        ], cls: 'small' },
        { t: 'photo', p: P.aso }
      ],
      source: '図は概念イメージ。実際の配管位置・爆発起点は未公表。',
      image: {
        kicker: 'イメージ 05',
        title: '配管のどこが壊れうるか',
        scene: 'pipes',
        caption: '赤い点は漏出しうる代表的な箇所。実際の配管経路・破断位置は公表されていない。',
        side: [
          { t: 'panel', tags: [['unknown', '調査で判明する項目']], items: [
            '破断面の形状（引張・せん断・腐食）',
            '破断が地震時か爆発時かの前後関係',
            '施工・保守の記録'
          ], cls: 'small' },
          slot('配管・ガス設備まわりの報道写真', 'assets/photos/pipes.jpg')
        ]
      }
    },

    /* 06 ------------------------------------------------------------- */
    {
      kicker: '不明点 02',
      title: '何が<br>着火源になった？',
      layout: 'split',
      ambient: 'spark',
      left: [
        { t: 'list', items: [
          '損傷した電気配線',
          '照明や空調のスイッチ',
          '冷蔵・厨房設備',
          '非常電源や復電時の火花'
        ] },
        { t: 'warning', html: '候補の列挙であり、どれも現時点では未確認。' }
      ],
      right: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          'ガスの着火に必要なエネルギーは<b>約0.3ミリジュール</b>ときわめて小さい',
          '静電気の火花でも十分に着火する',
          'そのため「火の気がなかった」ことは着火源がなかった証明にならない'
        ], cls: 'small' },
        { t: 'note', html: '着火源の特定は、電気系統の<b>溶融痕</b>など物証から追う。証拠が焼失していることも多い。' }
      ],
      source: '候補の列挙であり、どれも現時点では未確認。',
      image: {
        kicker: 'イメージ 06',
        title: '着火源の候補',
        scene: 'spark',
        caption: '溜まったガスが可燃範囲に入っているとき、ごく小さな火花でも着火しうる。どれが着火源だったかは特定されていない。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '停電から<b>復電した瞬間</b>は、機器が一斉に動き出すため火花が出やすい',
            '冷蔵庫のサーモスタットなど、無人でも動く機器がある'
          ], cls: 'small' },
          { t: 'photo', p: P.odaiba }
        ]
      }
    },

    /* 07 ------------------------------------------------------------- */
    {
      kicker: '不明点 03',
      title: '自動遮断は<br>作動したのか？',
      bg: P.odaiba.src,
      layout: 'split',
      ambient: 'meter',
      left: [
        { t: 'panel', items: [
          '地震時にガス供給を止める仕組みはどうなっていたか',
          '遮断前に大量漏出したのか',
          '遮断後も配管内の残留ガスが漏れたのか',
          '設備自体が損傷していたのか'
        ] }
      ],
      right: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          'マイコンメーターは<b>震度5相当</b>の揺れで自動遮断する',
          'ただし止まるのは<b>メーターより下流</b>だけ',
          '供給側（上流）の配管が壊れていれば、メーターでは止められない'
        ], cls: 'small' },
        { t: 'photo', p: P.meter1 }
      ],
      source: '背景は別災害の参考写真（Wikimedia Commons）。今回の現場ではありません。',
      image: {
        kicker: 'イメージ 07',
        title: '感震遮断が守れる範囲',
        scene: 'meter',
        caption: 'メーターが遮断できるのは下流側だけ。上流側の破断は、別の仕組み（地区ガバナ等）でしか止まらない。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '都市ガスは地区ガバナに感震遮断があり、地域単位で供給を止める',
            'LPガスはバルク貯槽・容器側にも遮断弁がある',
            '遮断しても、配管内に残ったガスは出てくる'
          ], cls: 'small' },
          { t: 'photo', p: P.meter2 }
        ]
      }
    },

    /* 08 ------------------------------------------------------------- */
    {
      kicker: '不明点 04',
      title: 'なぜ、避難後も<br>人が建物内に残った？',
      layout: 'split',
      ambient: 'people',
      left: [
        { t: 'panel', tags: [['confirmed', '報道']], items: [
          '約200人が避難した後に爆発したとの情報',
          '従業員らの安否確認が難航'
        ] },
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          '商業施設の避難は、客を出したあとに従業員が最終確認して残るのが通例',
          'そのため「最後に残るのは従業員」という構造がある'
        ], cls: 'tiny' },
        { t: 'note', html: '「戻った」「残された」など個別の行動は正式確認前。<b>断定しないこと</b>。' }
      ],
      right: [
        { t: 'panel', tags: [['unknown', '考えられる事情']], items: [
          '残留客の確認',
          '火元・ガス元栓の確認',
          '負傷者の救助',
          '店舗閉鎖作業'
        ] }
      ],
      source: '出典：初期報道（2026年7月29日時点）。避難人数・安否確認の状況は今後更新される可能性があります。',
      image: {
        kicker: 'イメージ 08',
        title: '避難の流れと、残る人',
        scene: 'people',
        caption: '客の避難が終わったあと、確認のために従業員が残る——という一般的な流れのイメージ。今回の個別行動は確認前。',
        side: [
          { t: 'panel', tags: [['unknown', '今後わかること']], items: [
            '館内放送の指示内容',
            '避難完了の判断を誰がしたか',
            '残っていた人数と位置'
          ], cls: 'small' },
          slot('避難の様子（報道映像のキャプチャ等）', 'assets/photos/evacuation.jpg')
        ]
      }
    },

    /* 09 ------------------------------------------------------------- */
    {
      kicker: '救助活動',
      title: '爆発だけではない。<br>余震下の崩落現場',
      lead: '救助隊は、崩れた構造物、ガス、火災、余震という複数の危険に同時対応する。',
      bg: P.noto.src,
      layout: 'full',
      ambient: 'rescue',
      guardBottom: true,
      body: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          'ガスが残っている場所では、火花を出す資機材が使えない',
          '余震のたびに隊員を退避させるため、作業は中断を繰り返す',
          '崩落現場では、支保工で支えながら少しずつ進む'
        ], cls: 'small' }
      ],
      source: '背景：能登半島地震の自衛隊救助活動（防衛省／Wikimedia Commons）。今回の現場ではありません。',
      image: {
        kicker: 'イメージ 09',
        title: '救助現場に同時に存在する危険',
        scene: 'rescue',
        caption: '余震・残留ガス・火災・二次崩落。どれかひとつでも作業を止める要因になる。',
        side: [
          { t: 'photo', p: P.ukisar },
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '救助の優先度は、生存の可能性が高い場所から',
            'ガス検知しながらでないと重機を入れられない'
          ], cls: 'tiny' }
        ]
      }
    },

    /* 10 ------------------------------------------------------------- */
    {
      kicker: '不明点 05',
      title: '崩れたのは<br>地震か、爆発か',
      layout: 'split',
      ambient: 'collapse',
      left: [
        { t: 'panel', tags: [['hypo', '地震による先行損傷']], items: [
          '天井・外壁・接合部の損傷',
          '鉄骨や設備支持部の変形',
          '配管破断'
        ], cls: 'small' },
        { t: 'warning', html: '最終的には、破断面・焼損・爆風方向を調べる構造鑑定が必要。' }
      ],
      right: [
        { t: 'panel', tags: [['hypo', '爆発圧力による破壊']], items: [
          '外壁の吹き飛び',
          '2階部分の崩落拡大',
          '破片の広範囲飛散'
        ], cls: 'small' },
        { t: 'panel', tags: [['knowledge', '見分け方']], items: [
          '地震の破壊は<b>水平方向</b>に、爆発の破壊は<b>放射状</b>に痕が残る',
          '破片が外向きに飛んでいれば、内側からの圧力を示す'
        ], cls: 'tiny' }
      ],
      source: '映像だけで「爆発が全部壊した」と断定するのは危険。',
      image: {
        kicker: 'イメージ 10',
        title: '壊し方が違う、ふたつの力',
        scene: 'collapse',
        caption: '地震は横に揺さぶり、爆発は内側から押す。残った痕跡の向きから、どちらがどこまで壊したかを切り分ける。',
        side: [
          { t: 'photo', p: P.magnitogorsk },
          { t: 'note', html: 'ガス爆発では、上階の床が抜けて<b>縦に崩れる</b>ことがある。地震の崩れ方とは形が違う。' }
        ]
      }
    },

    /* 11 ------------------------------------------------------------- */
    {
      kicker: '施設の背景',
      title: '2016年にも被災した<br>イオンモール熊本',
      bg: P.mall1.src,
      layout: 'split',
      ambient: 'history',
      left: [
        { t: 'panel', items: [
          '熊本県嘉島町の大型商業施設',
          '2016年熊本地震でも大きな被害',
          '復旧・改修を経て営業してきた'
        ] },
        { t: 'html', html: '<p class="caption">今回の損傷箇所が、旧部分・補強部分・改修部分のどこに当たるかは重要な検証点。</p>' }
      ],
      right: [
        { t: 'panel', tags: [['knowledge', '2016年熊本地震']], items: [
          '4月14日 M6.5（前震）、4月16日 M7.3（本震）',
          '<b>震度7を2回</b>観測した、観測史上まれな地震',
          '同じ建物が10年で二度、震度7級に遭ったことになる'
        ], cls: 'small' },
        { t: 'photo', p: P.kumamoto2016 }
      ],
      source: '背景：2022年の平時写真（Wikimedia Commons）',
      image: {
        kicker: 'イメージ 11',
        title: '被災 → 改修 → 再び被災',
        scene: 'history',
        caption: '2016年の被災、復旧・改修、そして2026年。どの時期に施工された部分が、今回どう壊れたかが検証点になる。',
        side: [
          { t: 'panel', tags: [['unknown', '検証される項目']], items: [
            '改修範囲の図面と施工記録',
            '定期点検・法定点検の結果',
            'ガス設備の更新履歴'
          ], cls: 'small' },
          { t: 'photo', p: P.mall2 }
        ]
      }
    },

    /* 12 ------------------------------------------------------------- */
    {
      kicker: '不明点 06',
      title: '過去の補強・改修は<br>今回どこまで機能した？',
      layout: 'full',
      ambient: 'retrofit',
      guardBottom: true,
      body: [
        { t: 'html', html: '<div class="quote">「耐震化されていた」ことと、<br>「二次爆発にも耐えられる」ことは同じではない。</div>' },
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          '耐震設計が想定するのは、主に地震の<b>水平力</b>',
          'ガス爆発は、内側からの<b>面圧</b>という別種の力を生む',
          '地震で弱った構造に爆発が重なる複合災害'
        ], cls: 'small' }
      ],
      source: '手抜き工事を示す証拠は現時点でない。検証前の断定は避ける。',
      image: {
        kicker: 'イメージ 12',
        title: '想定していた力と、実際にかかった力',
        scene: 'retrofit',
        caption: '筋かいは横揺れに効く。しかし内部爆発の面圧は、設計時の想定荷重には通常含まれない。',
        side: [
          { t: 'panel', tags: [['danger', '注意']], items: [
            '「壊れた＝手抜き」ではない',
            '設計の想定外の力がかかった可能性を、まず検討する'
          ], cls: 'small' },
          { t: 'note', html: '構造の検証は、設計図・施工記録・現物の破壊状況を突き合わせて行う。<b>結論が出るまで時間がかかる</b>。' }
        ]
      }
    },

    /* 13 ------------------------------------------------------------- */
    {
      kicker: '不明点 07',
      title: '火災報知・館内放送・<br>防火区画は機能した？',
      layout: 'split',
      ambient: 'alarm',
      left: [
        { t: 'panel', tags: [['unknown', '今後確認される項目']], items: [
          '感知器の発報時刻',
          '館内放送の内容と時刻',
          '防火扉・シャッターの状態',
          '排煙設備の動作'
        ], cls: 'small' },
        { t: 'note', html: '現段階で、設備の不作動を示す公式発表はありません。' }
      ],
      right: [
        { t: 'panel', tags: [['danger', '重要']], items: [
          '大規模施設では、設備単体より<b>複数システムが連鎖して機能したか</b>が問われる'
        ] },
        { t: 'photo', p: P.firedoor }
      ],
      source: '現段階で設備不作動を示す公式発表はありません。',
      image: {
        kicker: 'イメージ 13',
        title: '設備は「連鎖」で効く',
        scene: 'alarm',
        caption: '感知 → 放送 → 区画 → 排煙。どこか一段が働かないと、その先の効果も失われる。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '停電すると、非常電源に切り替わるまでの間、動かない設備がある',
            '防火扉は、物が挟まっていると閉まりきらない',
            '地震で建具が歪むと、扉が動かなくなることがある'
          ], cls: 'small' }
        ]
      }
    },

    /* 14 ------------------------------------------------------------- */
    {
      kicker: '不明点 08',
      title: 'ガス臭は、いつから<br>誰が把握していた？',
      layout: 'full',
      ambient: 'smell',
      guardBottom: true,
      body: [
        { t: 'timeline', items: [
          { b: 'A', s: '地震直後から？' },
          { b: 'B', s: '避難中に発覚？' },
          { b: 'C', s: '爆発直前？' },
          { b: 'D', s: '爆発後の現場臭？' }
        ] },
        { t: 'warning', html: '臭いの証言は重要だが、風向き・場所・時間が揃わないと漏出起点の特定には使えない。' },
        { t: 'note', html: '<b>一般知識：</b>ガスは本来<b>無臭</b>で、気づけるように付臭剤（メルカプタン類）を加えることが法令で義務づけられている。爆発する濃度のはるか手前で臭うように設計されている。' }
      ],
      source: '初期証言には混乱が含まれるため、消防の聞き取り結果を待つ必要があります。',
      image: {
        kicker: 'イメージ 14',
        title: '臭いから起点は特定できるか',
        scene: 'smell',
        caption: '臭いは風下へ流れる。証言の場所と時刻、そのときの風向きが揃って初めて、起点の推定材料になる。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '付臭剤は、爆発下限の<b>1000分の1</b>の濃度で臭ってわかるよう定められている',
            '一方で、強い臭いを嗅ぎ続けると<b>嗅覚が疲れて</b>感じにくくなる',
            'つまり「途中から臭わなくなった」証言も、矛盾とは限らない'
          ], cls: 'small' }
        ]
      }
    },

    /* 15 ------------------------------------------------------------- */
    {
      kicker: '爆発の特徴',
      title: '外壁が大きく壊れた理由',
      bg: P.gasexp.src,
      layout: 'split',
      ambient: 'pressure',
      left: [
        { t: 'panel', items: [
          '閉鎖空間でガスが燃焼すると内圧が急上昇',
          '比較的弱い外壁や開口部へ圧力が抜ける',
          '地震で損傷していた場合、破壊が拡大しやすい'
        ] }
      ],
      right: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          '建物のガス爆発の多くは<b>爆燃</b>（火炎が音速未満で広がる現象）',
          '一般的な外壁や間仕切りは、数kPa程度の圧力差で壊れる',
          '壁が壊れて圧力が抜けることで、かえって全壊を免れる場合もある'
        ], cls: 'small' },
        { t: 'photo', p: P.gasexp }
      ],
      source: '背景：海外の別のガス爆発（Wikimedia Commons）。今回の現場ではありません。',
      image: {
        kicker: 'イメージ 15',
        title: '圧力はいちばん弱いところへ抜ける',
        scene: 'pressure',
        caption: '閉じた空間で圧力が上がると、最初に壊れるのは一番弱い面。だから外壁が大きく飛ぶ。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '窓や軽い壁は「逃がし面」として働く',
            '逃げ場がないほど、構造本体への負荷が大きくなる'
          ], cls: 'small' },
          { t: 'photo', p: P.magnitogorsk }
        ]
      }
    },

    /* 16 ------------------------------------------------------------- */
    {
      kicker: '不明点 09',
      title: '「複数回の爆発音」<br>は何を意味する？',
      layout: 'split',
      ambient: 'sound',
      left: [
        { t: 'panel', tags: [['hypo', '仮説']], items: [
          '主爆発と二次的な破裂',
          '天井・外壁の連続崩落音',
          '別区画に広がった燃焼',
          '変圧器・設備の破損音'
        ] }
      ],
      right: [
        { t: 'panel', items: [
          '人が聞いた「爆発音」が、すべて化学的な爆発とは限らない'
        ] },
        { t: 'panel', tags: [['knowledge', '照合に使えるもの']], items: [
          '防犯カメラの音声トラック',
          '119番通報の受信時刻',
          '近隣の地震計・振動記録',
          'SNS動画のタイムスタンプ'
        ], cls: 'tiny' }
      ],
      source: '音声・監視カメラ・地震計・通報時刻の照合が必要。',
      image: {
        kicker: 'イメージ 16',
        title: '「何回鳴ったか」は何を示すか',
        scene: 'sound',
        caption: '複数のピークがあっても、そのすべてが爆発とは限らない。崩落音や設備の破損音も同じように聞こえる。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '音の記録は、時刻を確定できる数少ない客観データ',
            '複数地点の記録を突き合わせると、発生位置を絞れることがある'
          ], cls: 'small' }
        ]
      }
    },

    /* 17 ------------------------------------------------------------- */
    {
      kicker: '不明点 10',
      title: '監視カメラと<br>設備ログは残っているか',
      layout: 'split',
      ambient: 'cctv',
      left: [
        { t: 'panel', items: [
          '爆発前の人の動き',
          '煙や天井落下の発生位置',
          '電源停止・復旧の時刻',
          'ガス警報器・火災報知器の履歴',
          '避難放送と従業員連絡の記録'
        ] },
        { t: 'html', html: '<p class="caption">これらが回収できれば、事故の時系列は一気に具体化する。</p>' }
      ],
      right: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          'レコーダーは<b>上書き式</b>が一般的で、時間が経つと消える',
          '停電するとその時点で記録が止まる',
          '本体が焼損・水損していても、記録媒体だけ生きていることがある'
        ], cls: 'small' },
        { t: 'note', html: '記録媒体が損傷している可能性もある。だからこそ<b>早期の押収・保全</b>が重要になる。' }
      ],
      source: '記録媒体が損傷している可能性もある。',
      image: {
        kicker: 'イメージ 17',
        title: '残っていれば、時系列は確定する',
        scene: 'cctv',
        caption: '映像と設備ログは、証言と違って時刻がぶれない。回収できるかどうかが調査の分かれ目になる。',
        side: [
          { t: 'panel', tags: [['unknown', '未確認']], items: [
            '記録装置の設置位置と生存状況',
            '記録の保存期間',
            '回収済みかどうか'
          ], cls: 'small' }
        ]
      }
    },

    /* 18 ------------------------------------------------------------- */
    {
      kicker: 'もう一つの重要点',
      title: 'これは“単純な爆発事故”<br>ではない',
      lead: '巨大地震 → 建物・配管損傷 → 避難 → ガス蓄積 → 着火 → 崩落という、複合災害の可能性。',
      bg: P.kumamoto2016.src,
      layout: 'full',
      ambient: 'chain',
      guardBottom: true,
      body: [
        { t: 'panel', tags: [['knowledge', '一般知識']], items: [
          '複合災害は、ひとつひとつの対策が正しくても起きうる',
          'それぞれの段階は別の担当・別の法令にまたがっている',
          'だから「誰か一人の落ち度」に還元できないことが多い'
        ], cls: 'small' }
      ],
      source: '背景：2016年熊本地震の被害写真（Wikimedia Commons）。今回の現場ではありません。',
      image: {
        kicker: 'イメージ 18',
        title: '連鎖として見る',
        scene: 'chain',
        caption: '地震 → 損傷 → 避難 → 滞留 → 着火 → 崩落。ひとつの事故ではなく、つながった連鎖として捉える。',
        side: [
          { t: 'panel', tags: [['knowledge', '一般知識']], items: [
            '事故調査では、原因をひとつに絞らず<b>すべての段階</b>を検証する',
            '連鎖のどこを断てば止まったかが、再発防止策になる'
          ], cls: 'small' },
          { t: 'photo', p: P.aso }
        ]
      }
    },

    /* 19 ------------------------------------------------------------- */
    {
      kicker: '現時点の整理',
      title: '確定・有力・未判明を<br>混ぜない',
      layout: 'split',
      ambient: 'layers',
      left: [
        { t: 'panel', tags: [['confirmed', '確定に近い']], items: [
          'M7.1、最大震度7',
          'モールで爆発・崩落',
          '地震後に時間差'
        ], cls: 'small' },
        { t: 'panel', tags: [['hypo', '有力だが未確定']], items: [
          'ガス漏れが関与した可能性'
        ], cls: 'small' }
      ],
      right: [
        { t: 'panel', tags: [['unknown', 'まだ不明']], items: [
          '漏出箇所',
          '着火源',
          '遮断設備の状態',
          '崩壊の詳しい順序',
          '館内対応の全時系列'
        ], cls: 'small' }
      ],
      source: '2026年7月29日15時台までの公表・報道を基準に作成。',
      image: {
        kicker: 'イメージ 19',
        title: '確度で分けて置く',
        scene: 'layers',
        caption: '同じ画面で扱っても、確度のラベルは分けて示す。混ぜた瞬間に、推測が事実として広がる。',
        side: [
          { t: 'panel', tags: [['danger', 'やってはいけないこと']], items: [
            '未判明の項目を、断定形で語る',
            '仮説と報道内容を同じ強さで並べる',
            '出典を示さずに数字を出す'
          ], cls: 'small' }
        ]
      }
    },

    /* 20 ------------------------------------------------------------- */
    {
      kicker: '最後に',
      title: '最大の謎は<br><span class="hl-red">なぜ防げなかったのか</span>',
      lead: '地震そのものは止められない。だが、ガス漏れ・着火・避難後の二次災害は、どこかで連鎖を断てなかったのか。',
      bg: P.mall2.src,
      layout: 'full',
      ambient: 'chainbreak',
      guardBottom: true,
      body: [
        { t: 'warning', html: '原因調査が進めば内容は更新されます。陰謀・テロ・手抜き工事を示す根拠は、現時点では確認されていません。' }
      ],
      source: '主要参照：気象庁、消防・警察発表を引用した国内報道、毎日新聞、テレビ朝日、TBS NEWS DIG、熊本日日新聞',
      image: {
        kicker: 'イメージ 20',
        title: '断てたとすれば、どこか',
        scene: 'chainbreak',
        caption: '地震は止められない。しかし連鎖の途中には、断てたかもしれない箇所がある——それを探すのが事故調査。',
        side: [
          { t: 'panel', tags: [['knowledge', '調査はこれから']], items: [
            '消防・警察による実況見分と鑑定',
            '事業者・行政による検証',
            '結論が出るまで数週間〜数か月かかる'
          ], cls: 'small' },
          { t: 'note', html: 'この動画の内容も、<b>公式発表が出たら更新される前提</b>で作っている。' }
        ]
      }
    }
  ];

  global.SLIDES = SLIDES;
  global.PHOTOS = P;
})(window);
