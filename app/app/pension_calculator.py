from datetime import datetime, date

class AdvancedPensionCalculator:
    """Προχωρημένος αλγόριθμος υπολογισμού σύνταξης"""
    
    @staticmethod
    def calculate_advanced_pension(birth_date, start_date, salary_history, 
                                 marital_status, dependents=0, special_categories=None):
        """
        Προχωρημένος υπολογισμός σύνταξης με βάση πολλούς παράγοντες
        """
        try:
            # Βασικοί υπολογισμοί
            current_age = AdvancedPensionCalculator.calculate_age(birth_date)
            years_of_service = AdvancedPensionCalculator.calculate_years_of_service(start_date)
            
            # Υπολογισμός μέσου μισθού (τελευταία 5 χρόνια)
            recent_salaries = sorted(salary_history, key=lambda x: x[0], reverse=True)[:5]
            if recent_salaries:
                avg_salary = sum(salary for year, salary in recent_salaries) / len(recent_salaries)
            else:
                avg_salary = 0
            
            # Βασική σύνταξη
            base_pension = avg_salary * years_of_service * 0.02
            
            # Προσαυξήσεις
            dependent_bonus = dependents * (base_pension * 0.05)
            
            marital_bonus = 0
            if marital_status == 'married':
                marital_bonus = base_pension * 0.10
            elif marital_status == 'divorced_with_children':
                marital_bonus = base_pension * 0.08
            
            category_bonus = 0
            if special_categories:
                if 'military' in special_categories:
                    category_bonus = base_pension * 0.15
                elif 'public_sector' in special_categories:
                    category_bonus = base_pension * 0.10
            
            total_pension = base_pension + dependent_bonus + marital_bonus + category_bonus
            
            return {
                'base_pension': round(base_pension, 2),
                'dependent_bonus': round(dependent_bonus, 2),
                'marital_bonus': round(marital_bonus, 2),
                'category_bonus': round(category_bonus, 2),
                'total_pension': round(total_pension, 2),
                'retirement_age': AdvancedPensionCalculator.calculate_retirement_age(birth_date),
                'years_of_service': years_of_service,
                'average_salary': round(avg_salary, 2)
            }
        except Exception as e:
            return {'error': f'Calculation error: {str(e)}'}
    
    @staticmethod
    def calculate_retirement_age(birth_date):
        birth_year = birth_date.year
        if birth_year <= 1955:
            return 65
        elif 1956 <= birth_year <= 1965:
            return 66
        else:
            return 67
    
    @staticmethod
    def calculate_age(birth_date):
        today = date.today()
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
    
    @staticmethod
    def calculate_years_of_service(start_date):
        today = date.today()
        return today.year - start_date.year - (
            (today.month, today.day) < (start_date.month, start_date.day)
        )
    
    @staticmethod
    def pension_forecast(current_pension, inflation_rate=0.02, years=10):
        forecast = []
        for year in range(1, years + 1):
            future_value = current_pension * ((1 + inflation_rate) ** year)
            forecast.append({
                'year': datetime.now().year + year,
                'pension_value': round(future_value, 2),
                'cumulative_inflation': round(((1 + inflation_rate) ** year - 1) * 100, 2)
            })
        return forecast


class SimplePensionCalculator:
    """Απλός αλγόριθμος υπολογισμού σύνταξης για το σύστημα"""
    
    @staticmethod
    def calculate_basic_pension(current_age, retirement_age, current_salary, 
                               monthly_contribution, current_savings=0, 
                               expected_return=0.06, inflation_rate=0.02):
        """
        Απλός υπολογισμός σύνταξης με βάση βασικές παραμέτρους
        """
        try:
            # Μετατροπή ποσοστών
            annual_return = expected_return
            annual_inflation = inflation_rate
            
            # Βασικοί υπολογισμοί
            years_to_retirement = retirement_age - current_age
            months_to_retirement = years_to_retirement * 12
            
            # Υπολογισμός μελλοντικής αξίας τρεχουσών αποταμιεύσεων
            future_savings = current_savings * ((1 + annual_return) ** years_to_retirement)
            
            # Υπολογισμός μελλοντικής αξίας μηνιαίων εισφορών
            monthly_rate = annual_return / 12
            future_contributions = 0
            
            if monthly_rate > 0:
                future_contributions = monthly_contribution * (
                    ((1 + monthly_rate) ** months_to_retirement - 1) / monthly_rate
                ) * (1 + monthly_rate)
            else:
                future_contributions = monthly_contribution * months_to_retirement
            
            # Συνολική σύνταξη
            total_pension = future_savings + future_contributions
            
            # Μηνιαία σύνταξη (4% withdrawal rate)
            monthly_pension = total_pension * 0.04 / 12
            
            # Ρύθμιση για πληθωρισμό
            real_monthly_pension = monthly_pension / ((1 + annual_inflation) ** years_to_retirement)
            
            return {
                'total_pension': round(total_pension, 2),
                'monthly_pension': round(monthly_pension, 2),
                'real_monthly_pension': round(real_monthly_pension, 2),
                'future_savings': round(future_savings, 2),
                'future_contributions': round(future_contributions, 2),
                'years_to_retirement': years_to_retirement,
                'retirement_year': datetime.now().year + years_to_retirement,
                'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {'error': f'Calculation error: {str(e)}'}
    
    @staticmethod
    def calculate_required_contributions(target_pension, current_age, retirement_age, 
                                       current_savings=0, expected_return=0.06):
        """
        Υπολογισμός απαιτούμενων μηνιαίων εισφορών για συγκεκριμένη σύνταξη
        """
        try:
            years_to_retirement = retirement_age - current_age
            months_to_retirement = years_to_retirement * 12
            
            # Μελλοντική αξία τρεχουσών αποταμιεύσεων
            future_savings = current_savings * ((1 + expected_return) ** years_to_retirement)
            
            # Απαιτούμενη συνολική σύνταξη (βάσει 4% withdrawal rate)
            required_total = (target_pension * 12) / 0.04
            
            # Απαιτούμενες πρόσθετες εισφορές
            required_additional = max(0, required_total - future_savings)
            
            # Υπολογισμός μηνιαίας εισφοράς
            monthly_rate = expected_return / 12
            monthly_contribution = 0
            
            if monthly_rate > 0 and months_to_retirement > 0:
                monthly_contribution = required_additional / (
                    ((1 + monthly_rate) ** months_to_retirement - 1) / monthly_rate * (1 + monthly_rate)
                )
            
            return {
                'required_monthly_contribution': round(monthly_contribution, 2),
                'target_pension': target_pension,
                'required_total_pension': round(required_total, 2),
                'future_savings_value': round(future_savings, 2),
                'years_to_retirement': years_to_retirement
            }
            
        except Exception as e:
            return {'error': f'Calculation error: {str(e)}'}


# Βοηθητική συνάρτηση για συμβατότητα
def calculate_pension(*args, **kwargs):
    """Βοηθητική συνάρτηση για backward compatibility"""
    return SimplePensionCalculator.calculate_basic_pension(*args, **kwargs)