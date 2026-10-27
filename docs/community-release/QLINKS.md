# Q-Link reference

Generated from the exact installed BOTH FIX Q-Links.json. IDs are zero-based VST indices. Screen mappings are page-specific; logical Q-Link numbers are not sixteen physical encoders on an MPC One. Program mappings are preserved separately in QLINKS.json.

## PLAY physical-bank convention

This bank ordering comes from the existing A/B fix; the host focus rectangle remains a hardware check.

| Bank | Logical Q-Link numbers in physical order |
|---|---|
| A |13,9,5,1|
| B |14,10,6,2|
| C |15,11,7,3|
| D |16,12,8,4|

## PLAY

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|139|EVOLUTION|
|Q-Link 2|17|CORRUPT|
|Q-Link 3|138|Rest Bias|
|Q-Link 4|13|Window|
|Q-Link 5|53|MIX|
|Q-Link 6|9|BREAK|
|Q-Link 7|137|Cut Weight|
|Q-Link 8|79|Duration Max|
|Q-Link 9|133|CHARACTER|
|Q-Link 10|134|FRAGMENT|
|Q-Link 11|136|Reverse Weight|
|Q-Link 12|77|Chance|
|Q-Link 13|132|ACTIVITY|
|Q-Link 14|12|POSITION|
|Q-Link 15|135|Repeat Weight|
|Q-Link 16|140|Rate|

## BUFFER

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|128|Repeat|
|Q-Link 2|15|Bend|
|Q-Link 3|58|BufDice|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|127|Rec max|
|Q-Link 6|14|Reverse|
|Q-Link 7|57|Buffer|
|Q-Link 8|9|BREAK|
|Q-Link 9|11|Freeze|
|Q-Link 10|13|Window|
|Q-Link 11|17|CORRUPT|
|Q-Link 12|0|Length|
|Q-Link 13|126|Capture|
|Q-Link 14|12|POSITION|
|Q-Link 15|16|Pitch|
|Q-Link 16|1|Gate|

## EVENTS

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|138|Rest Bias|
|Q-Link 2|79|Duration Max|
|Q-Link 3|125|Distanc|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|137|Cut Weight|
|Q-Link 6|77|Chance|
|Q-Link 7|76|Density|
|Q-Link 8|-1|Unassigned|
|Q-Link 9|136|Reverse Weight|
|Q-Link 10|140|Rate|
|Q-Link 11|49|Ghost|
|Q-Link 12|-1|Unassigned|
|Q-Link 13|135|Repeat Weight|
|Q-Link 14|139|EVOLUTION|
|Q-Link 15|80|Rest|
|Q-Link 16|-1|Unassigned|

## MOTION

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|70|MDepth|
|Q-Link 2|73|Sync|
|Q-Link 3|59|MotDice|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|124|Rate|
|Q-Link 6|91|Route|
|Q-Link 7|72|MMax|
|Q-Link 8|-1|Unassigned|
|Q-Link 9|68|Type|
|Q-Link 10|90|MDest|
|Q-Link 11|71|MMin|
|Q-Link 12|-1|Unassigned|
|Q-Link 13|54|Motion|
|Q-Link 14|105|Source|
|Q-Link 15|74|Hold|
|Q-Link 16|-1|Unassigned|

## RANDOM

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|65|Prob|
|Q-Link 2|55|Chaos|
|Q-Link 3|-1|Unassigned|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|64|Depth|
|Q-Link 6|106|Dice|
|Q-Link 7|-1|Unassigned|
|Q-Link 8|-1|Unassigned|
|Q-Link 9|61|Random|
|Q-Link 10|67|Lock|
|Q-Link 11|-1|Unassigned|
|Q-Link 12|-1|Unassigned|
|Q-Link 13|60|Dest|
|Q-Link 14|66|Intvl|
|Q-Link 15|104|ChaosOn|
|Q-Link 16|-1|Unassigned|

## TIMING

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|25|Time|
|Q-Link 2|81|Reset|
|Q-Link 3|-1|Unassigned|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|24|Apply|
|Q-Link 6|33|Tempo|
|Q-Link 7|-1|Unassigned|
|Q-Link 8|-1|Unassigned|
|Q-Link 9|102|Clock|
|Q-Link 10|32|Sync|
|Q-Link 11|-1|Unassigned|
|Q-Link 12|-1|Unassigned|
|Q-Link 13|75|Seed|
|Q-Link 14|26|Grid|
|Q-Link 15|-1|Unassigned|
|Q-Link 16|-1|Unassigned|

## GLOBAL

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|29|Smooth|
|Q-Link 2|19|Density|
|Q-Link 3|94|Spacing|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|28|Drive|
|Q-Link 6|18|Chance|
|Q-Link 7|93|Sens|
|Q-Link 8|-1|Unassigned|
|Q-Link 9|5|Bypass|
|Q-Link 10|34|Seed|
|Q-Link 11|92|Listen|
|Q-Link 12|-1|Unassigned|
|Q-Link 13|3|Output|
|Q-Link 14|48|Engine|
|Q-Link 15|20|Mutate|
|Q-Link 16|-1|Unassigned|

## MIDI

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|46|FrzMode|
|Q-Link 2|95|LProb|
|Q-Link 3|-1|Unassigned|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|27|GateMod|
|Q-Link 6|94|Spacing|
|Q-Link 7|-1|Unassigned|
|Q-Link 8|-1|Unassigned|
|Q-Link 9|31|MIDI|
|Q-Link 10|93|Sens|
|Q-Link 11|97|LRepeat|
|Q-Link 12|-1|Unassigned|
|Q-Link 13|30|MIDI Ch|
|Q-Link 14|92|Listen|
|Q-Link 15|96|LCap|
|Q-Link 16|-1|Unassigned|

## SCENES

| Logical Q-Link | Parameter ID | Control |
|---|---:|---|
|Q-Link 1|35|Order|
|Q-Link 2|39|Step|
|Q-Link 3|-1|Unassigned|
|Q-Link 4|-1|Unassigned|
|Q-Link 5|23|StepDiv|
|Q-Link 6|38|StepDiv|
|Q-Link 7|-1|Unassigned|
|Q-Link 8|-1|Unassigned|
|Q-Link 9|22|Seq Run|
|Q-Link 10|37|Prob|
|Q-Link 11|-1|Unassigned|
|Q-Link 12|-1|Unassigned|
|Q-Link 13|21|State|
|Q-Link 14|36|Store|
|Q-Link 15|47|Recall|
|Q-Link 16|-1|Unassigned|
