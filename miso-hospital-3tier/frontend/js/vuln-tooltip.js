// data-vuln-title / data-vuln-desc / data-vuln-attack 속성이 붙은 .vuln-badge 요소에
// 마우스를 올리면(클릭 없이) 근처에 설명 팝업을 띄운다. 모든 페이지에서 공통으로 재사용.

// 팝업 DOM은 하나만 만들어서 위치와 내용만 바꿔가며 재사용 (매번 새로 생성하지 않음)
const tooltip = document.createElement('div');
tooltip.className = 'vuln-tooltip';
document.body.appendChild(tooltip);

function showTooltip(badge) {
  const { vulnTitle, vulnDesc, vulnAttack } = badge.dataset;
  tooltip.innerHTML = `
    <div class="vuln-tooltip__title">⚠ ${vulnTitle}</div>
    <div>${vulnDesc}</div>
    <div class="vuln-tooltip__label">공격 방법</div>
    <div>${vulnAttack}</div>
  `;
  tooltip.style.display = 'block';
  positionTooltip(badge);
}

function positionTooltip(badge) {
  const rect = badge.getBoundingClientRect();
  const tw = tooltip.offsetWidth;
  // 뱃지 오른쪽에 띄우되, 화면 밖으로 나가면 왼쪽으로 뒤집음
  const left = rect.right + tw + 20 > window.innerWidth ? rect.left - tw - 8 : rect.right + 8;
  tooltip.style.left = `${Math.max(8, left)}px`;
  tooltip.style.top = `${rect.top}px`;
}

function hideTooltip() {
  tooltip.style.display = 'none';
}

// 페이지 내 모든 뱃지에 이벤트 연결
document.querySelectorAll('.vuln-badge').forEach((badge) => {
  badge.addEventListener('mouseenter', () => showTooltip(badge));
  badge.addEventListener('mouseleave', hideTooltip);
});
