import re

def build_spaced_regex(digit_counts):
    # digit_counts = [6, 7] -> 6 digits, then 7 digits
    parts = []
    for count in digit_counts:
        part = r'[\s\-\~_]*'.join([r'\d'] * count)
        parts.append(part)
    return re.compile(r'(' + parts[0] + r')[\s\-\~_]*(' + parts[1] + r')')

def mask_pii(text: str) -> str:
    """
    사용자 입력 텍스트에서 PII(개인정보)를 탐지하고 마스킹 처리합니다.
    """
    if not text:
        return text

    masked_text = text

    # 1. 주민등록번호 (RRN)
    # \d 6번 + \d 7번
    rrn_pattern = build_spaced_regex([6, 7])
    masked_text = rrn_pattern.sub(r'\1-[MASKED]', masked_text)

    # 2. 전화번호 (Phone Number)
    # 010 (3) + 4 + 4
    # '0', '1', '[016789]'
    phone_part1 = r'0[\s\-\~_]*1[\s\-\~_]*[016789]'
    phone_part2 = r'[\s\-\~_]*'.join([r'\d'] * 3) + r'[\s\-\~_]*\d?' # 3 or 4 digits. Let's just use 4 digits for simplicity, or \d 4 times.
    phone_part2 = r'[\s\-\~_]*'.join([r'\d'] * 4)
    phone_part3 = r'[\s\-\~_]*'.join([r'\d'] * 4)
    phone_pattern = re.compile(f'({phone_part1})[\\s\\-\\~_]*({phone_part2})[\\s\\-\\~_]*({phone_part3})')
    masked_text = phone_pattern.sub(r'\1-****-\3', masked_text)

    # 3. 이름 (Name)
    name_pattern1 = re.compile(r'(이름은|이름이|저는|내 이름은)\s*([가-힣]{2,4})(\s*입니다|\s*이에요|\s*야|\s*라고)')
    def mask_name(match):
        prefix = match.group(1)
        name = match.group(2)
        suffix = match.group(3)
        return f"{prefix} {'*' * len(name)}{suffix}"
    
    masked_text = name_pattern1.sub(mask_name, masked_text)

    return masked_text

if __name__ == "__main__":
    # Test cases
    test_inputs = [
        "제 주민번호는 900101-1234567 입니다.",
        "제 번호는 9001011234567이에요.",
        "주민번호 9 0 0 1 0 1 - 1 2 3 4 5 6 7 입니다.",
        "전화번호는 010-1234-5678 입니다.",
        "연락처 01012345678",
        "저는 홍길동입니다."
    ]
    
    for t in test_inputs:
        print(f"Original: {t}")
        print(f"Masked  : {mask_pii(t)}")
        print("-")
