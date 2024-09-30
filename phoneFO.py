import phonenumbers
from phonenumbers import geocoder, carrier, timezone, is_valid_number
from phonenumbers.phonenumberutil import number_type, PhoneNumberType

def phone_lookup(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        country = geocoder.description_for_number(parsed_number, "ru")
        operator = carrier.name_for_number(parsed_number, "ru")
        timezones = timezone.time_zones_for_number(parsed_number)
        timezones_str = ", ".join(timezones)
        valid_number = is_valid_number(parsed_number)
        phone_type = number_type(parsed_number)
        phone_type_str = (
            "Мобильный" if phone_type == PhoneNumberType.MOBILE else
            "Стационарный" if phone_type == PhoneNumberType.FIXED_LINE else
            "Неизвестный тип"
        )
        international_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        response = (
            f"📱\n"
            f"├ Номер: {phone_number}\n"
            f"├ Международный формат: {international_format}\n"
            f"├ Страна: {country}\n"
            f"├ Оператор: {operator if operator else 'Не определено'}\n"
            f"├ Часовой пояс: {timezones_str}\n"
            f"├ Действительный номер: {'Да' if valid_number else 'Нет'}\n"
            f"└ Тип номера: {phone_type_str}\n\n"
        )

        return response, phone_number  # Возвращаем оригинальный номер

    except Exception as e:
        return f"Ошибка обработки номера. Убедитесь, что номер введен в правильном формате. Ошибка: {str(e)}", None