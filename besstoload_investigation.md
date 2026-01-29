# BESS-to-Load Jump Investigation Report

================================================================================
LIFETIME SHEET - BESSTOLOAD INVESTIGATION
================================================================================

### Row Labels in Lifetime Sheet (Column A):
  Row 1: Year
  Row 2: SolarGen_MWh
  Row 3: SolarToLoad_MWh
  Row 4: BESSToLoad_MWh
  Row 5: NonGridEnergyUse_MWh
  Row 6: GridEnergyUse_MWh
  Row 7: TotalLoad_MWh
  Row 8: SolarOffset_pct
  Row 9: BESSContribution_pct
  Row 10: CleanEnergyShare_pct
  Row 11: GridSupplyShare_pct
  Row 12: ExcessSolarExport_MWh
  Row 13: SolarToLoad_Std_MWh
  Row 14: SolarToLoad_Peak_MWh
  Row 15: BESSToLoad_Std_MWh
  Row 16: BESSToLoad_Peak_MWh
  Row 17: BESSToLoad_OffPeak_MWh
  Row 18: GridToBESS_MWh
  Row 19: GridToBESS_OffPeak_MWh
  Row 20: GridToBESS_Normal_MWh
  Row 21: SolarToBESS_MWh
  Row 22: NetSolarToBESS_MWh
  Row 23: BESS ConvLoss Annual
  Row 24: DPPA
  Row 25: Q_Khc
  Row 26: Surplus

### Found besstoload at Row 4

### Column Headers (Row 1):
  Col A: Year
  Col B: 1
  Col C: 2
  Col D: 3
  Col E: 4
  Col F: 5
  Col G: 6
  Col H: 7
  Col I: 8
  Col J: 9
  Col K: 10
  Col L: 11
  Col M: 12
  Col N: 13
  Col O: 14
  Col P: 15
  Col Q: 16
  Col R: 17
  Col S: 18
  Col T: 19
  Col U: 20
  Col V: 21
  Col W: 22
  Col X: 23
  Col Y: 24
  Col Z: 25

### All Rows - Values Across Years:
--------------------------------------------------------------------------------

**Row 2: SolarGen_MWh**
  Y1:71808.2986 | Y2:70372.1327 | Y3:69977.1870 | Y4:69582.2414 | Y5:69187.2957
  Y6:68792.3501 | Y7:68397.4044 | Y8:68002.4588 | Y9:67607.5132 | Y10:67212.5675
  Y11:66817.6219 | Y12:66422.6762 | Y13:66027.7306 | Y14:65632.7849 | Y15:65237.8393
  Y16:64842.8937 | Y17:64447.9480 | Y18:64053.0024 | Y19:63658.0567 | Y20:63263.1111
  Y21:62868.1654 | Y22:62473.2198 | Y23:62078.2742 | Y24:61683.3285 | Y25:61288.3829

**Row 3: SolarToLoad_MWh**
  Y1:61106.3824 | Y2:59884.2547 | Y3:59548.1696 | Y4:59212.0845 | Y5:58875.9994
  Y6:58539.9143 | Y7:58203.8292 | Y8:57867.7441 | Y9:57531.6590 | Y10:57195.5739
  Y11:56859.4888 | Y12:56523.4037 | Y13:56187.3186 | Y14:55851.2335 | Y15:55515.1484
  Y16:55179.0633 | Y17:54842.9782 | Y18:54506.8931 | Y19:54170.8080 | Y20:53834.7229
  Y21:53498.6378 | Y22:53162.5526 | Y23:52826.4675 | Y24:52490.3824 | Y25:52154.2973

**Row 4: BESSToLoad_MWh**
  Y1:8677.2229 | Y2:8455.9537 | Y3:8143.0834 | Y4:7965.5642 | Y5:7801.0753
  Y6:7639.5931 | Y7:7481.4535 | Y8:7326.5874 | Y9:7174.9270 | Y10:7026.4060
  Y11:8455.9537 | Y12:8281.3383 | Y13:8105.7739 | Y14:7942.0373 | Y15:7777.6371
  Y16:7616.6400 | Y17:7458.9756 | Y18:7304.5748 | Y19:7154.8310 | Y20:7009.5879
  Y21:6868.6952 | Y22:8455.9537 | Y23:8287.6803 | Y24:8123.5842 | Y25:7962.7372
  ⚠️ JUMP Y10→Y11: 7026.4060 → 8455.9537 (+20.35%)
  ⚠️ JUMP Y21→Y22: 6868.6952 → 8455.9537 (+23.11%)

**Row 5: NonGridEnergyUse_MWh**
  Y1:69783.6053 | Y2:68340.2084 | Y3:67691.2530 | Y4:67177.6487 | Y5:66677.0747
  Y6:66179.5074 | Y7:65685.2827 | Y8:65194.3315 | Y9:64706.5860 | Y10:64221.9799
  Y11:65315.4425 | Y12:64804.7420 | Y13:64293.0925 | Y14:63793.2708 | Y15:63292.7855
  Y16:62795.7033 | Y17:62301.9537 | Y18:61811.4678 | Y19:61325.6390 | Y20:60844.3108
  Y21:60367.3330 | Y22:61618.5064 | Y23:61114.1478 | Y24:60613.9666 | Y25:60117.0346

**Row 6: GridEnergyUse_MWh**
  Y1:114478.6704 | Y2:115922.0672 | Y3:116571.0226 | Y4:117084.6269 | Y5:117585.2009
  Y6:118082.7683 | Y7:118576.9929 | Y8:119067.9441 | Y9:119555.6896 | Y10:120040.2957
  Y11:118946.8331 | Y12:119457.5337 | Y13:119969.1831 | Y14:120469.0049 | Y15:120969.4901
  Y16:121466.5723 | Y17:121960.3219 | Y18:122450.8078 | Y19:122936.6367 | Y20:123417.9648
  Y21:123894.9427 | Y22:122643.7692 | Y23:123148.1278 | Y24:123648.3090 | Y25:124145.2411

**Row 7: TotalLoad_MWh**
  Y1:184262.2756 | Y2:184262.2756 | Y3:184262.2756 | Y4:184262.2756 | Y5:184262.2756
  Y6:184262.2756 | Y7:184262.2756 | Y8:184262.2756 | Y9:184262.2756 | Y10:184262.2756
  Y11:184262.2756 | Y12:184262.2756 | Y13:184262.2756 | Y14:184262.2756 | Y15:184262.2756
  Y16:184262.2756 | Y17:184262.2756 | Y18:184262.2756 | Y19:184262.2756 | Y20:184262.2756
  Y21:184262.2756 | Y22:184262.2756 | Y23:184262.2756 | Y24:184262.2756 | Y25:184262.2756

**Row 8: SolarOffset_pct**
  Y1:0.3316 | Y2:0.3250 | Y3:0.3232 | Y4:0.3213 | Y5:0.3195
  Y6:0.3177 | Y7:0.3159 | Y8:0.3141 | Y9:0.3122 | Y10:0.3104
  Y11:0.3086 | Y12:0.3068 | Y13:0.3049 | Y14:0.3031 | Y15:0.3013
  Y16:0.2995 | Y17:0.2976 | Y18:0.2958 | Y19:0.2940 | Y20:0.2922
  Y21:0.2903 | Y22:0.2885 | Y23:0.2867 | Y24:0.2849 | Y25:0.2830

**Row 9: BESSContribution_pct**
  Y1:0.0471 | Y2:0.0459 | Y3:0.0442 | Y4:0.0432 | Y5:0.0423
  Y6:0.0415 | Y7:0.0406 | Y8:0.0398 | Y9:0.0389 | Y10:0.0381
  Y11:0.0459 | Y12:0.0449 | Y13:0.0440 | Y14:0.0431 | Y15:0.0422
  Y16:0.0413 | Y17:0.0405 | Y18:0.0396 | Y19:0.0388 | Y20:0.0380
  Y21:0.0373 | Y22:0.0459 | Y23:0.0450 | Y24:0.0441 | Y25:0.0432
  ⚠️ JUMP Y10→Y11: 0.0381 → 0.0459 (+20.35%)
  ⚠️ JUMP Y21→Y22: 0.0373 → 0.0459 (+23.11%)

**Row 10: CleanEnergyShare_pct**
  Y1:0.3787 | Y2:0.3709 | Y3:0.3674 | Y4:0.3646 | Y5:0.3619
  Y6:0.3592 | Y7:0.3565 | Y8:0.3538 | Y9:0.3512 | Y10:0.3485
  Y11:0.3545 | Y12:0.3517 | Y13:0.3489 | Y14:0.3462 | Y15:0.3435
  Y16:0.3408 | Y17:0.3381 | Y18:0.3355 | Y19:0.3328 | Y20:0.3302
  Y21:0.3276 | Y22:0.3344 | Y23:0.3317 | Y24:0.3290 | Y25:0.3263

**Row 11: GridSupplyShare_pct**
  Y1:0.6213 | Y2:0.6291 | Y3:0.6326 | Y4:0.6354 | Y5:0.6381
  Y6:0.6408 | Y7:0.6435 | Y8:0.6462 | Y9:0.6488 | Y10:0.6515
  Y11:0.6455 | Y12:0.6483 | Y13:0.6511 | Y14:0.6538 | Y15:0.6565
  Y16:0.6592 | Y17:0.6619 | Y18:0.6645 | Y19:0.6672 | Y20:0.6698
  Y21:0.6724 | Y22:0.6656 | Y23:0.6683 | Y24:0.6710 | Y25:0.6737

**Row 12: ExcessSolarExport_MWh**
  Y1:1087.2648 | Y2:1065.5196 | Y3:1059.5396 | Y4:1053.5596 | Y5:1047.5797
  Y6:1041.5997 | Y7:1035.6198 | Y8:1029.6398 | Y9:1023.6599 | Y10:1017.6799
  Y11:1011.6999 | Y12:1005.7200 | Y13:999.7400 | Y14:993.7601 | Y15:987.7801
  Y16:981.8002 | Y17:975.8202 | Y18:969.8402 | Y19:963.8603 | Y20:957.8803
  Y21:951.9004 | Y22:945.9204 | Y23:939.9405 | Y24:933.9605 | Y25:927.9805

**Row 13: SolarToLoad_Std_MWh**
  Y1:48919.6704 | Y2:47941.2770 | Y3:47672.2188 | Y4:47403.1606 | Y5:47134.1024
  Y6:46865.0442 | Y7:46595.9860 | Y8:46326.9279 | Y9:46057.8697 | Y10:45788.8115
  Y11:45519.7533 | Y12:45250.6951 | Y13:44981.6369 | Y14:44712.5787 | Y15:44443.5205
  Y16:44174.4624 | Y17:43905.4042 | Y18:43636.3460 | Y19:43367.2878 | Y20:43098.2296
  Y21:42829.1714 | Y22:42560.1132 | Y23:42291.0550 | Y24:42021.9969 | Y25:41752.9387

**Row 14: SolarToLoad_Peak_MWh**
  Y1:12186.7120 | Y2:11942.9777 | Y3:11875.9508 | Y4:11808.9239 | Y5:11741.8970
  Y6:11674.8701 | Y7:11607.8432 | Y8:11540.8162 | Y9:11473.7893 | Y10:11406.7624
  Y11:11339.7355 | Y12:11272.7086 | Y13:11205.6817 | Y14:11138.6547 | Y15:11071.6278
  Y16:11004.6009 | Y17:10937.5740 | Y18:10870.5471 | Y19:10803.5202 | Y20:10736.4932
  Y21:10669.4663 | Y22:10602.4394 | Y23:10535.4125 | Y24:10468.3856 | Y25:10401.3587

**Row 15: BESSToLoad_Std_MWh**
  Y1:1239.0860 | Y2:1207.4893 | Y3:1162.8122 | Y4:1137.4629 | Y5:1113.9743
  Y6:1090.9150 | Y7:1068.3330 | Y8:1046.2186 | Y9:1024.5618 | Y10:1003.3534
  Y11:1207.4893 | Y12:1182.5546 | Y13:1157.4845 | Y14:1134.1033 | Y15:1110.6273
  Y16:1087.6374 | Y17:1065.1233 | Y18:1043.0752 | Y19:1021.6922 | Y20:1000.9518
  Y21:980.8327 | Y22:1207.4893 | Y23:1183.4602 | Y24:1160.0277 | Y25:1137.0592
  ⚠️ JUMP Y10→Y11: 1003.3534 → 1207.4893 (+20.35%)
  ⚠️ JUMP Y21→Y22: 980.8327 → 1207.4893 (+23.11%)

**Row 16: BESSToLoad_Peak_MWh**
  Y1:7438.1369 | Y2:7248.4645 | Y3:6980.2713 | Y4:6828.1014 | Y5:6687.1011
  Y6:6548.6781 | Y7:6413.1204 | Y8:6280.3688 | Y9:6150.3652 | Y10:6023.0526
  Y11:7248.4645 | Y12:7098.7837 | Y13:6948.2895 | Y14:6807.9340 | Y15:6667.0098
  Y16:6529.0027 | Y17:6393.8523 | Y18:6261.4996 | Y19:6133.1388 | Y20:6008.6361
  Y21:5887.8625 | Y22:7248.4645 | Y23:7104.2200 | Y24:6963.5565 | Y25:6825.6780
  ⚠️ JUMP Y10→Y11: 6023.0526 → 7248.4645 (+20.35%)
  ⚠️ JUMP Y21→Y22: 5887.8625 → 7248.4645 (+23.11%)

**Row 17: BESSToLoad_OffPeak_MWh**
  Y1:0.0000 | Y2:0.0000 | Y3:0.0000 | Y4:0.0000 | Y5:0.0000
  Y6:0.0000 | Y7:0.0000 | Y8:0.0000 | Y9:0.0000 | Y10:0.0000
  Y11:0.0000 | Y12:0.0000 | Y13:0.0000 | Y14:0.0000 | Y15:0.0000
  Y16:0.0000 | Y17:0.0000 | Y18:0.0000 | Y19:0.0000 | Y20:0.0000
  Y21:0.0000 | Y22:0.0000 | Y23:0.0000 | Y24:0.0000 | Y25:0.0000

**Row 18: GridToBESS_MWh**
  Y1:0.0000 | Y2:0.0000 | Y3:0.0000 | Y4:0.0000 | Y5:0.0000
  Y6:0.0000 | Y7:0.0000 | Y8:0.0000 | Y9:0.0000 | Y10:0.0000
  Y11:0.0000 | Y12:0.0000 | Y13:0.0000 | Y14:0.0000 | Y15:0.0000
  Y16:0.0000 | Y17:0.0000 | Y18:0.0000 | Y19:0.0000 | Y20:0.0000
  Y21:0.0000 | Y22:0.0000 | Y23:0.0000 | Y24:0.0000 | Y25:0.0000

**Row 19: GridToBESS_OffPeak_MWh**
  Y1:0.0000 | Y2:0.0000 | Y3:0.0000 | Y4:0.0000 | Y5:0.0000
  Y6:0.0000 | Y7:0.0000 | Y8:0.0000 | Y9:0.0000 | Y10:0.0000
  Y11:0.0000 | Y12:0.0000 | Y13:0.0000 | Y14:0.0000 | Y15:0.0000
  Y16:0.0000 | Y17:0.0000 | Y18:0.0000 | Y19:0.0000 | Y20:0.0000
  Y21:0.0000 | Y22:0.0000 | Y23:0.0000 | Y24:0.0000 | Y25:0.0000

**Row 20: GridToBESS_Normal_MWh**
  Y1:0.0000 | Y2:0.0000 | Y3:0.0000 | Y4:0.0000 | Y5:0.0000
  Y6:0.0000 | Y7:0.0000 | Y8:0.0000 | Y9:0.0000 | Y10:0.0000
  Y11:0.0000 | Y12:0.0000 | Y13:0.0000 | Y14:0.0000 | Y15:0.0000
  Y16:0.0000 | Y17:0.0000 | Y18:0.0000 | Y19:0.0000 | Y20:0.0000
  Y21:0.0000 | Y22:0.0000 | Y23:0.0000 | Y24:0.0000 | Y25:0.0000

**Row 21: SolarToBESS_MWh**
  Y1:9614.6514 | Y2:9422.3584 | Y3:9369.4778 | Y4:9316.5972 | Y5:9263.7167
  Y6:9210.8361 | Y7:9157.9555 | Y8:9105.0749 | Y9:9052.1943 | Y10:8999.3137
  Y11:8946.4332 | Y12:8893.5526 | Y13:8840.6720 | Y14:8787.7914 | Y15:8734.9108
  Y16:8682.0302 | Y17:8629.1497 | Y18:8576.2691 | Y19:8523.3885 | Y20:8470.5079
  Y21:8417.6273 | Y22:8364.7467 | Y23:8311.8662 | Y24:8258.9856 | Y25:8206.1050

**Row 22: NetSolarToBESS_MWh**
  Y1:9133.9189 | Y2:8951.2405 | Y3:8901.0039 | Y4:8850.7674 | Y5:8800.5308
  Y6:8750.2943 | Y7:8700.0577 | Y8:8649.8212 | Y9:8599.5846 | Y10:8549.3480
  Y11:8499.1115 | Y12:8448.8749 | Y13:8398.6384 | Y14:8348.4018 | Y15:8298.1653
  Y16:8247.9287 | Y17:8197.6922 | Y18:8147.4556 | Y19:8097.2191 | Y20:8046.9825
  Y21:7996.7460 | Y22:7946.5094 | Y23:7896.2729 | Y24:7846.0363 | Y25:7795.7997

**Row 23: BESS ConvLoss Annual**
  Y1:1976.4942 | Y2:1926.0936 | Y3:1854.8281 | Y4:1814.3928 | Y5:1776.9256
  Y6:1740.1433 | Y7:1704.1223 | Y8:1668.8470 | Y9:1634.3018 | Y10:1600.4718
  Y11:1926.0936 | Y12:1886.3197 | Y13:1846.3298 | Y14:1809.0339 | Y15:1771.5869
  Y16:1734.9150 | Y17:1699.0023 | Y18:1663.8330 | Y19:1629.7244 | Y20:1596.6410
  Y21:1564.5485 | Y22:1926.0936 | Y23:1887.7643 | Y24:1850.3866 | Y25:1813.7489
  ⚠️ JUMP Y10→Y11: 1600.4718 → 1926.0936 (+20.35%)
  ⚠️ JUMP Y21→Y22: 1564.5485 → 1926.0936 (+23.11%)

**Row 24: DPPA**

**Row 25: Q_Khc**
  Y1:66754.7053 | Y2:65419.6112 | Y3:65052.4604 | Y4:64685.3095 | Y5:64318.1586
  Y6:63951.0077 | Y7:63583.8568 | Y8:63216.7060 | Y9:62849.5551 | Y10:62482.4042
  Y11:62115.2533 | Y12:61748.1024 | Y13:61380.9516 | Y14:61013.8007 | Y15:60646.6498
  Y16:60279.4989 | Y17:59912.3480 | Y18:59545.1972 | Y19:59178.0463 | Y20:58810.8954
  Y21:58443.7445 | Y22:58076.5936 | Y23:57709.4428 | Y24:57342.2919 | Y25:56975.1410

**Row 26: Surplus**
  Y1:882.5455 | Y2:864.8946 | Y3:860.0406 | Y4:855.1866 | Y5:850.3326
  Y6:845.4786 | Y7:840.6246 | Y8:835.7706 | Y9:830.9166 | Y10:826.0626
  Y11:821.2086 | Y12:816.3546 | Y13:811.5006 | Y14:806.6466 | Y15:801.7926
  Y16:796.9386 | Y17:792.0846 | Y18:787.2306 | Y19:782.3766 | Y20:777.5226
  Y21:772.6686 | Y22:767.8146 | Y23:762.9606 | Y24:758.1066 | Y25:753.2526

================================================================================
FORMULA ANALYSIS
================================================================================

**Row 2: SolarGen_MWh**
  Year 1 (Col B): =Total_Solar_Generation*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 71808.29862859994
  Year 10 (Col K): =Total_Solar_Generation*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 67212.56751636957
  Year 11 (Col L): =Total_Solar_Generation*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 66817.62187391227
  Year 21 (Col V): =Total_Solar_Generation*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 62868.165449339314
  Year 22 (Col W): =Total_Solar_Generation*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 62473.21980688202

**Row 3: SolarToLoad_MWh**
  Year 1 (Col B): =Direct_PV_Consumption*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 61106.38235360867
  Year 10 (Col K): =Direct_PV_Consumption*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 57195.57388297774
  Year 11 (Col L): =Direct_PV_Consumption*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 56859.488780032894
  Year 21 (Col V): =Direct_PV_Consumption*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 53498.63775058444
  Year 22 (Col W): =Direct_PV_Consumption*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 53162.552647639604

**Row 4: BESSToLoad_MWh**
  Year 1 (Col B): =BESS_To_Load*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 8677.222913506528
  Year 10 (Col K): =BESS_To_Load*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 7026.406049490573
  Year 11 (Col L): =BESS_To_Load*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 8455.953729212113
  Year 21 (Col V): =BESS_To_Load*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 6868.69520800762
  Year 22 (Col W): =BESS_To_Load*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 8455.953729212113

**Row 5: NonGridEnergyUse_MWh**
  Year 1 (Col B): =B3+B4
    → Value: 69783.6052671152
  Year 10 (Col K): =K3+K4
    → Value: 64221.97993246831
  Year 11 (Col L): =L3+L4
    → Value: 65315.44250924501
  Year 21 (Col V): =V3+V4
    → Value: 60367.332958592066
  Year 22 (Col W): =W3+W4
    → Value: 61618.506376851714

**Row 6: GridEnergyUse_MWh**
  Year 1 (Col B): =B7-B5+B18
    → Value: 114478.67035199044
  Year 10 (Col K): =K7-K5+K18
    → Value: 120040.29568663733
  Year 11 (Col L): =L7-L5+L18
    → Value: 118946.83310986063
  Year 21 (Col V): =V7-V5+V18
    → Value: 123894.94266051357
  Year 22 (Col W): =W7-W5+W18
    → Value: 122643.76924225393

**Row 7: TotalLoad_MWh**
  Year 1 (Col B): =Total_Factory_Load/1000
    → Value: 184262.27561910564
  Year 10 (Col K): =Total_Factory_Load/1000
    → Value: 184262.27561910564
  Year 11 (Col L): =Total_Factory_Load/1000
    → Value: 184262.27561910564
  Year 21 (Col V): =Total_Factory_Load/1000
    → Value: 184262.27561910564
  Year 22 (Col W): =Total_Factory_Load/1000
    → Value: 184262.27561910564

**Row 8: SolarOffset_pct**
  Year 1 (Col B): =B3/B7
    → Value: 0.3316271990470996
  Year 10 (Col K): =K3/K7
    → Value: 0.31040305830808534
  Year 11 (Col L): =L3/L7
    → Value: 0.3085791087133263
  Year 21 (Col V): =V3/V7
    → Value: 0.29033961276573594
  Year 22 (Col W): =W3/W7
    → Value: 0.288515663170977

**Row 9: BESSContribution_pct**
  Year 1 (Col B): =B4/B7
    → Value: 0.047091695163059256
  Year 10 (Col K): =K4/K7
    → Value: 0.03813263472342586
  Year 11 (Col L): =L4/L7
    → Value: 0.04589085693640125
  Year 21 (Col V): =V4/V7
    → Value: 0.03727673060006117
  Year 22 (Col W): =W4/W7
    → Value: 0.04589085693640125

**Row 10: CleanEnergyShare_pct**
  Year 1 (Col B): =B5/B7
    → Value: 0.37871889421015886
  Year 10 (Col K): =K5/K7
    → Value: 0.3485356930315112
  Year 11 (Col L): =L5/L7
    → Value: 0.3544699656497276
  Year 21 (Col V): =V5/V7
    → Value: 0.32761634336579715
  Year 22 (Col W): =W5/W7
    → Value: 0.3344065201073782

**Row 11: GridSupplyShare_pct**
  Year 1 (Col B): =B6/B7
    → Value: 0.6212811057898412
  Year 10 (Col K): =K6/K7
    → Value: 0.6514643069684888
  Year 11 (Col L): =L6/L7
    → Value: 0.6455300343502725
  Year 21 (Col V): =V6/V7
    → Value: 0.6723836566342029
  Year 22 (Col W): =W6/W7
    → Value: 0.6655934798926219

**Row 12: ExcessSolarExport_MWh**
  Year 1 (Col B): =PV_Surplus*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 1087.2648472831695
  Year 10 (Col K): =PV_Surplus*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 1017.679897057047
  Year 11 (Col L): =PV_Surplus*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 1011.6999403969896
  Year 21 (Col V): =PV_Surplus*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 951.9003737964159
  Year 22 (Col W): =PV_Surplus*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 945.9204171363584

**Row 13: SolarToLoad_Std_MWh**
  Year 1 (Col B): =Direct_PV_Std*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 48919.6703807746
  Year 10 (Col K): =Direct_PV_Std*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 45788.81147640505
  Year 11 (Col L): =Direct_PV_Std*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 45519.75328931079
  Year 21 (Col V): =Direct_PV_Std*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 42829.17141836821
  Year 22 (Col W): =Direct_PV_Std*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 42560.11323127395

**Row 14: SolarToLoad_Peak_MWh**
  Year 1 (Col B): =Direct_PV_Peak*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 12186.711972834051
  Year 10 (Col K): =Direct_PV_Peak*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 11406.762406572676
  Year 11 (Col L): =Direct_PV_Peak*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 11339.73549072209
  Year 21 (Col V): =Direct_PV_Peak*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 10669.466332216223
  Year 22 (Col W): =Direct_PV_Peak*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 10602.439416365636

**Row 15: BESSToLoad_Std_MWh**
  Year 1 (Col B): =BESStoLoad_Std*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1239.085963800919
  Year 10 (Col K): =BESStoLoad_Std*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1003.3533998922413
  Year 11 (Col L): =BESStoLoad_Std*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1207.4892717239957
  Year 21 (Col V): =BESStoLoad_Std*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 980.8326819196071
  Year 22 (Col W): =BESStoLoad_Std*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1207.4892717239957

**Row 16: BESSToLoad_Peak_MWh**
  Year 1 (Col B): =BESStoLoad_Peak*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 7438.13694970561
  Year 10 (Col K): =BESStoLoad_Peak*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 6023.052649598333
  Year 11 (Col L): =BESStoLoad_Peak*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 7248.464457488117
  Year 21 (Col V): =BESStoLoad_Peak*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 5887.8625260880135
  Year 22 (Col W): =BESStoLoad_Peak*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 7248.464457488117

**Row 17: BESSToLoad_OffPeak_MWh**
  Year 1 (Col B): =BESStoLoad_Off_Peak*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 10 (Col K): =BESStoLoad_Off_Peak*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 11 (Col L): =BESStoLoad_Off_Peak*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 21 (Col V): =BESStoLoad_Off_Peak*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 22 (Col W): =BESStoLoad_Off_Peak*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0

**Row 18: GridToBESS_MWh**
  Year 1 (Col B): =Grid_To_BESS*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 10 (Col K): =Grid_To_BESS*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 11 (Col L): =Grid_To_BESS*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 21 (Col V): =Grid_To_BESS*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 22 (Col W): =Grid_To_BESS*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0

**Row 19: GridToBESS_OffPeak_MWh**
  Year 1 (Col B): =GridtoBESS_Off_Peak*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 10 (Col K): =GridtoBESS_Off_Peak*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 11 (Col L): =GridtoBESS_Off_Peak*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 21 (Col V): =GridtoBESS_Off_Peak*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 22 (Col W): =GridtoBESS_Off_Peak*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0

**Row 20: GridToBESS_Normal_MWh**
  Year 1 (Col B): =GridtoBESS_Std*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 10 (Col K): =GridtoBESS_Std*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 11 (Col L): =GridtoBESS_Std*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 21 (Col V): =GridtoBESS_Std*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0
  Year 22 (Col W): =GridtoBESS_Std*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 0

**Row 21: SolarToBESS_MWh**
  Year 1 (Col B): =Solar_To_BESS*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 9614.651427708048
  Year 10 (Col K): =Solar_To_BESS*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 8999.313736334738
  Year 11 (Col L): =Solar_To_BESS*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 8946.433153482343
  Year 21 (Col V): =Solar_To_BESS*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 8417.627324958405
  Year 22 (Col W): =Solar_To_BESS*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 8364.746742106012

**Row 22: NetSolarToBESS_MWh**
  Year 1 (Col B): =B21*Charge_discharge_efficiency
    → Value: 9133.918856322645
  Year 10 (Col K): =K21*Charge_discharge_efficiency
    → Value: 8549.348049518001
  Year 11 (Col L): =L21*Charge_discharge_efficiency
    → Value: 8499.111495808225
  Year 21 (Col V): =V21*Charge_discharge_efficiency
    → Value: 7996.745958710484
  Year 22 (Col W): =W21*Charge_discharge_efficiency
    → Value: 7946.509405000711

**Row 23: BESS ConvLoss Annual**
  Year 1 (Col B): =Usable_BESS_Capacity*365*System_Availability*Measures!$D$22*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1976.4941624999692
  Year 10 (Col K): =Usable_BESS_Capacity*365*System_Availability*Measures!$D$22*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1600.4717959424288
  Year 11 (Col L): =Usable_BESS_Capacity*365*System_Availability*Measures!$D$22*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1926.0935613562199
  Year 21 (Col V): =Usable_BESS_Capacity*365*System_Availability*Measures!$D$22*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1564.5484872224445
  Year 22 (Col W): =Usable_BESS_Capacity*365*System_Availability*Measures!$D$22*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$F$3:$F$27,0,0)/1000
    → Value: 1926.0935613562199

**Row 24: DPPA**

**Row 25: Q_Khc**
  Year 1 (Col B): =Measures!$G$11*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 66754.70534215546
  Year 10 (Col K): =Measures!$G$11*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 62482.40420025754
  Year 11 (Col L): =Measures!$G$11*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 62115.25332087569
  Year 21 (Col V): =Measures!$G$11*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 58443.74452705717
  Year 22 (Col W): =Measures!$G$11*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 58076.59364767532

**Row 26: Surplus**
  Year 1 (Col B): =Measures!$G$17*_xlfn.XLOOKUP(B$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 882.5454983735159
  Year 10 (Col K): =Measures!$G$17*_xlfn.XLOOKUP(K$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 826.0625864776113
  Year 11 (Col L): =Measures!$G$17*_xlfn.XLOOKUP(L$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 821.208586236557
  Year 21 (Col V): =Measures!$G$17*_xlfn.XLOOKUP(V$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 772.6685838260139
  Year 22 (Col W): =Measures!$G$17*_xlfn.XLOOKUP(W$1,Loss!$A$3:$A$27,Loss!$E$3:$E$27,0,0)/1000
    → Value: 767.8145835849598

================================================================================
LOSS SHEET - DEGRADATION FACTORS
================================================================================

### Loss Sheet Structure:

Column Headers (Row 1 or 2):
  Col A: R1=Loss Table , R2=Year , R3=1
  Col B: R1=None, R2=Battery's Loss, R3=None
  Col C: R1=None, R2=Battery, R3=1
  Col D: R1=None, R2=PV Loss, R3=None
  Col E: R1=None, R2=PV, R3=1
  Col F: R1=11, R2=Battery wt Replacement, R3=1

### Loss Data (Rows 3-27) - Columns A through H:
  Year  | Battery's Loss | Battery | PV Loss | PV | Battery wt Replacement | ColG | ColH
  ------------------------------------------------------------
  Row 3: 1 | - | 1 | - | 1 | 1 | - | -
  Row 4: 2 | 0.0255 | 0.9745 | 0.0200 | 0.9800 | 0.9745 | - | -
  Row 5: 3 | 0.0370 | 0.9375 | 0.0055 | 0.9745 | 0.9384 | - | -
  Row 6: 4 | 0.0218 | 0.9157 | 0.0055 | 0.9690 | 0.9180 | - | -
  Row 7: 5 | 0.0206 | 0.8951 | 0.0055 | 0.9635 | 0.8990 | - | -
  Row 8: 6 | 0.0207 | 0.8743 | 0.0055 | 0.9580 | 0.8804 | - | -
  Row 9: 7 | 0.0207 | 0.8537 | 0.0055 | 0.9525 | 0.8622 | - | -
  Row 10: 8 | 0.0207 | 0.8329 | 0.0055 | 0.9470 | 0.8443 | - | -
  Row 11: 9 | 0.0207 | 0.8123 | 0.0055 | 0.9415 | 0.8269 | - | -
  Row 12: 10 | 0.0207 | 0.7915 | 0.0055 | 0.9360 | 0.8098 | - | -
  Row 13: 11 | 0.0206 | 0.7709 | 0.0055 | 0.9305 | 0.9745 | - | -
  Row 14: 12 | 0.0207 | 0.7502 | 0.0055 | 0.9250 | 0.9544 | - | -
  Row 15: 13 | 0.0212 | 0.7290 | 0.0055 | 0.9195 | 0.9341 | - | -
  Row 16: 14 | 0.0202 | 0.7088 | 0.0055 | 0.9140 | 0.9153 | - | -
  Row 17: 15 | 0.0207 | 0.6882 | 0.0055 | 0.9085 | 0.8963 | - | -
  Row 18: 16 | 0.0207 | 0.6674 | 0.0055 | 0.9030 | 0.8778 | - | -
  Row 19: 17 | 0.0207 | 0.6467 | 0.0055 | 0.8975 | 0.8596 | - | -
  Row 20: 18 | 0.0207 | 0.6260 | 0.0055 | 0.8920 | 0.8418 | - | -
  Row 21: 19 | 0.0205 | 0.6055 | 0.0055 | 0.8865 | 0.8246 | - | -
  Row 22: 20 | 0.0203 | 0.5852 | 0.0055 | 0.8810 | 0.8078 | - | -
  Row 23: 21 | 0.0201 | 0.5651 | 0.0055 | 0.8755 | 0.7916 | - | -
  Row 24: 22 | 0.0200 | 0.5451 | 0.0055 | 0.8700 | 0.9745 | - | -
  Row 25: 23 | 0.0199 | 0.5252 | 0.0055 | 0.8645 | 0.9551 | - | -
  Row 26: 24 | 0.0198 | 0.5054 | 0.0055 | 0.8590 | 0.9362 | - | -
  Row 27: 25 | 0.0198 | 0.4856 | 0.0055 | 0.8535 | 0.9177 | - | -

### Loss Sheet - Degradation Jump Analysis:
  Battery (Col C): Y10=0.7915 → Y11=0.7709 (-2.61%)
  Battery (Col C): Y21=0.5651 → Y22=0.5451 (-3.54%)
  Battery wt Replacement (Col F): Y10=0.8098 → Y11=0.9745 (+20.35%)
  Battery wt Replacement (Col F): Y21=0.7916 → Y22=0.9745 (+23.11%)

================================================================================
OTHER INPUT SHEET - AUGMENTATION SCHEDULE
================================================================================

### Searching for Augmentation/MRA related data:
  Row 1: A:MRA Build-up Assumption