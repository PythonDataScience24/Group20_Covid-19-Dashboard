netto_lohn_col = 'B'
netto_lohn_row = '27'
start_row = 40
end_row = start_row + 8

result = '$B${}*($A${}/100)'.format(start_row, start_row)

for i in range(start_row + 1, end_row+1):
    result += ' + MIN($B${},MAX(0,{}{}-SUM($B${}:$B${})))*($A${}/100)'.format(i, netto_lohn_col, netto_lohn_row, start_row, i - 1, i)


dbs_start_row = 50
dbs_end_row = dbs_start_row + 5

dbs = '0'
netto_lohn_row = '28'
for i in range(dbs_start_row, dbs_end_row):
    dbs += ' + SIGN(MAX(0,{}{}-$A${}))*MAX(0,SIGN($A${}-{}{}))*($B${}+(({}{}-$A${})/100)*$C${})'.format(netto_lohn_col, netto_lohn_row,
                                                                                               i, i+ 1, netto_lohn_col, netto_lohn_row,
                                                                                                i, netto_lohn_col, netto_lohn_row,i,i)
print(result)
print(dbs)