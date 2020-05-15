import json
import os
from Divination import parameters
from Divination.DataOperations.AnalysisHelpers.cagr_calculator import cagrs_for_schemes
from Divination.DataOperations.helper_functions import fund_type_to_key_words, redeemed_amount_for
from Divination.DataOperations.Parse.filter_schemes import FilterSchemes


class InvestmentPerformance:
    FUNDS_DIVERSIFICATION: int = 3  # Top 'N' number of funds will be invested.
    filtered_schemes = {}

    def __init__(self, fund_type: str):
        self.fund_type = fund_type
        self.key_words = fund_type_to_key_words(self.fund_type)

    def return_on_investment(self, investment_amount: float, final_redeemed_date: str,
                             minimum_historical_days: int, investment_lifecycle_days: int,
                             fund_diversification=3):
        self.FUNDS_DIVERSIFICATION = fund_diversification
        self.filtered_schemes = FilterSchemes().filter_schemes_for_keywords(self.key_words,
                                                                            final_redeemed_date,
                                                                            minimum_historical_days +
                                                                            investment_lifecycle_days)
        start_index = self.filtered_schemes[0]['startIndex']
        end_index = self.filtered_schemes[0]['endIndex']
        print(start_index - investment_lifecycle_days, end_index)

        index = start_index - investment_lifecycle_days
        while index - investment_lifecycle_days > end_index:
            cagrs = cagrs_for_schemes(index + investment_lifecycle_days, index, self.filtered_schemes)
            sorted_funds = sorted(cagrs.items(), key=lambda x: x[1], reverse=True)
            investment_amount = self.calculate_redeemed_amount(investment_amount, index,
                                                               index - investment_lifecycle_days, sorted_funds)
            index -= investment_lifecycle_days

        cagrs = cagrs_for_schemes(index + investment_lifecycle_days, index, self.filtered_schemes)
        sorted_funds = sorted(cagrs.items(), key=lambda x: x[1], reverse=True)
        self.calculate_redeemed_amount(investment_amount, index, end_index, sorted_funds)
        index = end_index
        print(investment_amount, index)

    def calculate_redeemed_amount(self, investment_amount: int, start_index: int, end_index: int, sorted_funds: []):
        redeemed_amount = 0
        for fund in sorted_funds[0: self.FUNDS_DIVERSIFICATION]:
            with open(os.path.join(parameters.RAW_DATA_PATH, fund[0] + ".json")) as raw_data_file:
                scheme_data = json.load(raw_data_file)
                data = scheme_data['data']
                redeemed_amount += redeemed_amount_for(investment_amount / self.FUNDS_DIVERSIFICATION,
                                                       data[start_index], data[end_index])

        return redeemed_amount

    def average_return_on_investment(self, investment_amount: int, investment_lifecycle_days: int):
        if len(self.filtered_schemes) == 0:
            print("No Filtered Schemes")
            return

        redeemed_amount = 0
        for scheme in self.filtered_schemes:
            with open(os.path.join(parameters.RAW_DATA_PATH, str(scheme['scheme_code']) + ".json")) as raw_data_file:
                scheme_data = json.load(raw_data_file)
                start = scheme_data['data'][scheme['startIndex'] - investment_lifecycle_days]
                end = scheme_data['data'][scheme['endIndex']]
                redeemed_amount += redeemed_amount_for(investment_amount / len(self.filtered_schemes),
                                                       start, end)

        print('Average Performance =', redeemed_amount)


def main():
    performance = InvestmentPerformance('Equity')
    performance.return_on_investment(investment_amount=100000, final_redeemed_date='31-12-2019',
                                     minimum_historical_days=2000, investment_lifecycle_days=165)
    performance.average_return_on_investment(investment_amount=100000, investment_lifecycle_days=165)


if __name__ == '__main__':
    main()
