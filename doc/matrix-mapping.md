# マトリクス row/col マッピング

col番号(0〜5)を埋めてください。行の対応が間違っていたら訂正してください。

## 左側 (row0〜row3)

| 行 | 左→右の順のSW | col番号(左から順に) |
|---|---|---|
| row0 | SW1, SW4, SW7, SW11, SW15, SW18 | col0, col1, col2, col3, col4, col5 |
| row1 | SW2, SW5, SW8, SW12, SW16, SW19 | col0, col1, col2, col3, col4, col5|
| row2 | SW3, SW6, SW9, SW13, SW17, SW20 | col0, col1, col2, col3, col4, col5|
| row3(親指) | SW10, SW14, SW21 | col2,col3,col5 |

## 右側 (row4〜row7)

| 行 | 左→右の順のSW | col番号(左から順に) |
|---|---|---|
| row4 | SW22, SW26, SW29, SW33, SW37, SW40 | col5,col4,col3,col2,col1,col0 |
| row5 | SW23, SW27, SW30, SW34, SW38, SW41 | col5,col4,col3,col2,col1,col0  |
| row6 | SW24, SW28, SW31, SW35, SW39, SW42 |col5,col4,col3,col2,col1,col0  |
| row7(親指) | SW25, SW32, SW36 | col5,col3,col2 |

備考:
- 各行が col0, col1, col2, col3, col4, col5 の順にそのまま並んでいるなら、`row0: 0,1,2,3,4,5` のように書くだけでOK
- 親指行(row3, row7)はキーが3個しかないので、6個のcolのうちどれを使っているか(例: col2,3,5など)を教えてください
