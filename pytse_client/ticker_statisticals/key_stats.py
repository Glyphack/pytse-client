# میانگین: ave
# ارزش: val
# معاملات: trans
# رتبه: rank
# حجم: vol
# دفعات: numof
# روزانه: daily
# وزن: w
# قیمت: price
# منفی: neg
# مثبت: pos
# حقوقی: corporation
# حقیقی: individual
# بسته: close
# باز: open


class KeyStats:
    # name : id
    ave_val_trans_last_3_month = 1
    ave_val_trans_last_12_month = 2
    rank_val_trans_last_3_month = 3
    rank_val_trans_last_12_month = 4

    ave_vol_trans_last_3_month = 5
    ave_vol_trans_last_12_month = 6
    rank_vol_trans_last_3_month = 7
    rank_vol_trans_last_12_month = 8

    ave_numof_trans_last_3_month = 9
    ave_numof_trans_last_12_month = 10
    rank_numof_trans_last_3_month = 11
    rank_numof_trans_last_12_month = 12

    w_ave_price_last_day_normal = 13
    w_ave_price_last_day_base_vol = 14

    val_trans_last_day = 15
    vol_trans_last_day = 16
    numof_trans_last_day = 17

    numof_neg_days_last_3_month = 18
    numof_neg_days_last_12_month = 19
    percent_neg_days_last_3_month = 20
    percent_neg_days_last_12_month = 21
    rank_neg_days_last_3_month = 22
    rank_neg_days_last_12_month = 23

    numof_notrade_days_last_3_month = 24
    numof_notrade_days_last_12_month = 25

    numof_pos_days_last_3_month = 26
    numof_pos_days_last_12_month = 27
    percent_pos_days_last_3_month = 28
    percent_pos_days_last_12_month = 29
    rank_pos_days_last_3_month = 30
    rank_pos_days_last_12_month = 31

    numof_trade_days_last_3_month = 32
    numof_trade_days_last_12_month = 33

    rank_trade_days_last_3_month = 34
    rank_trade_days_last_12_month = 35

    val_company_last_day = 36
    rank_val_company_last_day = 37

    numof_open_days_last_3_month = 38
    numof_open_days_last_12_month = 39
    percent_open_days_last_3_month = 40
    percent_open_days_last_12_month = 41
    rank_open_days_last_3_month = 42
    rank_open_days_last_12_month = 43

    numof_close_days_last_3_month = 44
    numof_close_days_last_12_month = 45
    percent_close_days_last_3_month = 46
    percent_close_days_last_12_month = 47
    rank_close_days_last_3_month = 48
    rank_close_days_last_12_month = 49

    ave_vol_individual_buy_last_3_month = 50
    ave_vol_individual_buy_last_12_month = 51
    rank_vol_individual_buy_last_3_month = 52
    rank_vol_individual_buy_last_12_month = 53

    ave_vol_corporation_buy_last_3_month = 54
    ave_vol_corporation_buy_last_12_month = 55
    rank_vol_corporation_buy_last_3_month = 56
    rank_vol_corporation_buy_last_12_month = 57

    ave_numof_individual_buyer_last_3_month = 58
    ave_numof_individual_buyer_last_12_month = 59
    rank_numof_individual_buyer_last_3_month = 60
    rank_numof_individual_buyer_last_12_month = 61

    ave_numof_corporation_buyer_last_3_month = 62
    ave_numof_corporation_buyer_last_12_month = 63
    rank_numof_corporation_buyer_last_3_month = 64
    rank_numof_corporation_buyer_last_12_month = 65

    ave_numof_buyer_last_3_month = 66
    ave_numof_buyer_last_12_month = 67
    rank_numof_buyer_last_3_month = 68
    rank_numof_buyer_last_12_month = 69

    ave_vol_individual_sell_last_3_month = 70
    ave_vol_individual_sell_last_12_month = 71
    rank_vol_individual_sell_last_3_month = 72
    rank_vol_individual_sell_last_12_month = 73

    ave_vol_corporation_sell_last_3_month = 74
    ave_vol_corporation_sell_last_12_month = 75
    rank_vol_corporation_sell_last_3_month = 76
    rank_vol_corporation_sell_last_12_month = 77

    ave_numof_individual_seller_last_3_month = 78
    ave_numof_individual_seller_last_12_month = 79
    rank_numof_individual_seller_last_3_month = 80
    rank_numof_individual_seller_last_12_month = 81

    ave_numof_corporation_seller_last_3_month = 82
    ave_numof_corporation_seller_last_12_month = 83
    rank_numof_corporation_seller_last_3_month = 84
    rank_numof_corporation_seller_last_12_month = 85

    ave_numof_seller_last_3_month = 86
    ave_numof_seller_last_12_month = 87
    rank_numof_seller_last_3_month = 88
    rank_numof_seller_last_12_month = 89


filter_class = KeyStats()

# collect all var names of filter_class
keys = [attr for attr in dir(filter_class) if not attr.startswith("__")]
# convert filter_class to dict
filter_key_value = {getattr(filter_class, key): key for key in keys}
filter_value_NONE = {key: None for key in filter_key_value.values()}

if __name__ == "__main__":
    print(filter_key_value)
