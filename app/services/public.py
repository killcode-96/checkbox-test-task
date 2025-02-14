from app.database import db, models


def format_receipt_text(receipt: models.Receipt, line_length: int) -> str:
    """Formats a receipt as a text."""

    lines = []
    # Відцентровуємо заголовок
    lines.append(f"{'ФОП Checkbox Test Task':^{line_length}}")
    lines.append("=" * line_length)

    for i, product in enumerate(receipt.products):
        total_price = round(product.quantity * product.price, 2)

        # --- Лінії з назвою товару ---
        # Якщо назва довша за line_length, "розбиваємо" її на кілька рядків
        name = product.name
        while name:
            lines.append(f"{name[:line_length]:<{line_length}}")
            name = name[line_length:]

        # --- Лінія з кількістю, ціною та підсумком ---
        # Ліва частина: "3.00 x 298.00 ="
        left_part = f"{product.quantity:4.2f} x {product.price:6.2f} ="
        # Форматована підсумкова ціна"
        right_part = f"{total_price:7.2f}"

        # Підрахунок відступу між left_part та right_part
        space = line_length - len(left_part) - len(right_part)
        if space < 1:
            space = 1

        # Формуємо рядок, де total_price буде праворуч
        line2 = f"{left_part}{' ' * space}{right_part}"
        lines.append(line2)

        # Роздільна лінія між товарами, крім останнього
        if i < len(receipt.products) - 1:
            lines.append("-" * line_length)

    lines.append("=" * line_length)

    # Підсумкові значення
    def summary_line(label: str, amount: float) -> str:
        """Ліворуч - назва, праворуч - число з двома знаками після коми."""
        amount_str = f"{amount:9.2f}"
        space = line_length - len(label) - len(amount_str)
        if space < 1:
            space = 1
        return f"{label}{' ' * space}{amount_str}"

    total = float(receipt.total)
    payment_type_str = "Картка" if receipt.payment_type == "cashless" else "Готівка"
    payment_amount = float(receipt.payment_amount)
    rest = float(receipt.rest)

    lines.append(summary_line("СУМА", total))
    lines.append(summary_line(payment_type_str, payment_amount))
    lines.append(summary_line("Решта", rest))

    lines.append("=" * line_length)
    # Дата і час по центру
    lines.append(f"{receipt.created_at.strftime('%d.%m.%Y %H:%M'):^{line_length}}")
    # Подяка по центру
    lines.append(f"{'Дякуємо за покупку!':^{line_length}}")

    return "\n".join(lines)
