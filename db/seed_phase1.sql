-- =============================================================
-- Phase 1 Seed Data (v6.0) — SPC/CAPA/OEE/알림/알림설정
-- =============================================================

-- ─── SPC 규칙 (10건: 5개 품목 × 2개 검사항목) ───────────────
INSERT INTO spc_rules (item_code, check_name, rule_type, ucl, lcl, target, sample_size) VALUES
('ITM-00001', '외경', 'XBAR_R', 10.15, 9.85, 10.00, 5),
('ITM-00001', '무게', 'XBAR_R', 105.0, 95.0, 100.0, 5),
('ITM-00002', '외경', 'XBAR_R', 20.10, 19.90, 20.00, 5),
('ITM-00002', '두께', 'XBAR_R', 2.55, 2.45, 2.50, 5),
('ITM-00003', '길이', 'XBAR_R', 50.30, 49.70, 50.00, 5),
('ITM-00003', '무게', 'XBAR_R', 210.0, 190.0, 200.0, 5),
('ITM-00004', '외경', 'XBAR_R', 15.08, 14.92, 15.00, 5),
('ITM-00004', '경도', 'XBAR_R', 65.0, 55.0, 60.0, 5),
('ITM-00005', '두께', 'XBAR_R', 5.12, 4.88, 5.00, 5),
('ITM-00005', '무게', 'XBAR_R', 55.0, 45.0, 50.0, 5)
ON CONFLICT DO NOTHING;

-- ─── SPC 위반 이력 (20건) ────────────────────────────────────
INSERT INTO spc_violations (rule_id, violation_type, measured_value, subgroup_no, severity, resolved) VALUES
(1, 'RULE_1_BEYOND_3SIGMA', 10.22, 5, 'CRITICAL', TRUE),
(1, 'RULE_4_8_CONSECUTIVE_ONE_SIDE', 10.08, 12, 'WARNING', TRUE),
(2, 'RULE_1_BEYOND_3SIGMA', 108.5, 3, 'CRITICAL', FALSE),
(2, 'RULE_2_2OF3_BEYOND_2SIGMA', 104.2, 7, 'WARNING', FALSE),
(3, 'RULE_1_BEYOND_3SIGMA', 20.15, 2, 'CRITICAL', TRUE),
(3, 'RULE_3_4OF5_BEYOND_1SIGMA', 20.06, 8, 'WARNING', TRUE),
(4, 'RULE_1_BEYOND_3SIGMA', 2.58, 4, 'CRITICAL', FALSE),
(5, 'RULE_4_8_CONSECUTIVE_ONE_SIDE', 50.15, 10, 'WARNING', TRUE),
(5, 'RULE_1_BEYOND_3SIGMA', 50.35, 15, 'CRITICAL', FALSE),
(6, 'RULE_2_2OF3_BEYOND_2SIGMA', 212.0, 6, 'WARNING', TRUE),
(7, 'RULE_1_BEYOND_3SIGMA', 15.12, 3, 'CRITICAL', TRUE),
(7, 'RULE_3_4OF5_BEYOND_1SIGMA', 15.05, 9, 'WARNING', FALSE),
(8, 'RULE_1_BEYOND_3SIGMA', 67.0, 2, 'CRITICAL', TRUE),
(8, 'RULE_4_8_CONSECUTIVE_ONE_SIDE', 62.0, 11, 'WARNING', FALSE),
(9, 'RULE_1_BEYOND_3SIGMA', 5.15, 5, 'CRITICAL', TRUE),
(9, 'RULE_2_2OF3_BEYOND_2SIGMA', 5.10, 8, 'WARNING', TRUE),
(10, 'RULE_1_BEYOND_3SIGMA', 57.0, 4, 'CRITICAL', FALSE),
(10, 'RULE_3_4OF5_BEYOND_1SIGMA', 53.5, 7, 'WARNING', FALSE),
(1, 'RULE_2_2OF3_BEYOND_2SIGMA', 10.13, 18, 'WARNING', FALSE),
(3, 'RULE_4_8_CONSECUTIVE_ONE_SIDE', 20.05, 14, 'WARNING', TRUE)
ON CONFLICT DO NOTHING;

-- ─── CAPA (10건: 상태별 2건씩) ──────────────────────────────
INSERT INTO capa (capa_id, capa_type, source_type, source_id, title, description, status, priority, assigned_to, due_date, created_by) VALUES
('CAPA-20260301-001', 'CORRECTIVE', 'SPC_VIOLATION', '1', 'ITM-00001 외경 관리한계 초과', '연속 3σ 초과 발생, 설비 점검 필요', 'OPEN', 'HIGH', 'worker01', '2026-03-15', 'mgr02'),
('CAPA-20260301-002', 'PREVENTIVE', 'INSPECTION', NULL, '원자재 입고검사 기준 강화', '불량률 증가 추세에 대한 예방 조치', 'OPEN', 'MID', 'mgr02', '2026-03-20', 'admin'),
('CAPA-20260302-001', 'CORRECTIVE', 'EQUIP_DOWN', 'EQP-001', 'EQP-001 설비 고장 원인 조사', '진동 이상 감지 후 다운 발생', 'INVESTIGATION', 'HIGH', 'worker02', '2026-03-10', 'mgr01'),
('CAPA-20260302-002', 'CORRECTIVE', 'SPC_VIOLATION', '7', 'ITM-00004 외경 변동 분석', 'Cpk 1.0 미만으로 공정능력 부족', 'INVESTIGATION', 'MID', 'worker01', '2026-03-18', 'mgr02'),
('CAPA-20260303-001', 'CORRECTIVE', 'DEFECT', NULL, '용접 불량 시정 조치', '용접부 크랙 다발, 작업 표준 재정립 필요', 'ACTION', 'HIGH', 'worker01', '2026-03-12', 'mgr01'),
('CAPA-20260303-002', 'PREVENTIVE', 'AI_WARNING', NULL, 'AI 불량예측 기반 예방보전', 'XGBoost 모델 경고, 선제적 대응', 'ACTION', 'LOW', 'mgr01', '2026-03-25', 'admin'),
('CAPA-20260304-001', 'CORRECTIVE', 'SPC_VIOLATION', '9', 'ITM-00005 두께 불량 검증', '시정 조치 완료 후 효과 검증 중', 'VERIFICATION', 'MID', 'mgr02', '2026-03-08', 'mgr02'),
('CAPA-20260304-002', 'PREVENTIVE', 'INSPECTION', NULL, '공정검사 주기 단축', '품질 향상을 위한 검사 빈도 증가 검증', 'VERIFICATION', 'LOW', 'worker02', '2026-03-22', 'mgr01'),
('CAPA-20260228-001', 'CORRECTIVE', 'DEFECT', NULL, '도장 불량 시정 완료', '도장 두께 편차 개선, Cpk 1.5 이상 달성', 'CLOSED', 'HIGH', 'worker01', '2026-02-28', 'mgr02'),
('CAPA-20260228-002', 'PREVENTIVE', 'EQUIP_DOWN', 'EQP-005', '예방보전 계획 수립 완료', '분기별 설비 점검 계획 수립 및 승인', 'CLOSED', 'MID', 'mgr01', '2026-02-28', 'admin')
ON CONFLICT DO NOTHING;

-- ─── CAPA 조치 이력 (30건: CAPA당 3건) ──────────────────────
INSERT INTO capa_actions (capa_id, action_type, description, result, performed_by) VALUES
('CAPA-20260301-001', 'ROOT_CAUSE', '외경 편차 원인 분석 — 절삭공구 마모 의심', NULL, 'worker01'),
('CAPA-20260301-001', 'ROOT_CAUSE', '공구 교환 주기 확인 — 권장 대비 150% 초과 사용', NULL, 'worker01'),
('CAPA-20260301-001', 'CORRECTIVE', '공구 교환 주기 1000→700개로 단축 조치 예정', NULL, 'mgr02'),
('CAPA-20260301-002', 'ROOT_CAUSE', '원자재 불량률 추세 분석', NULL, 'mgr02'),
('CAPA-20260301-002', 'PREVENTIVE', '입고검사 샘플 수 5→10개 증가', NULL, 'mgr02'),
('CAPA-20260301-002', 'PREVENTIVE', '공급업체 품질 기준서 개정', NULL, 'admin'),
('CAPA-20260302-001', 'ROOT_CAUSE', '진동 데이터 분석 — 베어링 마모 확인', NULL, 'worker02'),
('CAPA-20260302-001', 'ROOT_CAUSE', '베어링 교환 이력 확인 — 권장 수명 초과', NULL, 'worker02'),
('CAPA-20260302-001', 'CORRECTIVE', '베어링 교환 조치 예정 (3/10)', NULL, 'mgr01'),
('CAPA-20260302-002', 'ROOT_CAUSE', 'Cpk 분석 — 공정 산포 과다', NULL, 'worker01'),
('CAPA-20260302-002', 'ROOT_CAUSE', '설비 조건 변동 확인', NULL, 'worker01'),
('CAPA-20260302-002', 'CORRECTIVE', '설비 세팅 표준화 작업 진행 중', NULL, 'mgr02'),
('CAPA-20260303-001', 'ROOT_CAUSE', '용접 전류/전압 분석', '전류 불안정 확인', 'worker01'),
('CAPA-20260303-001', 'CORRECTIVE', '용접기 전원부 교체', '교체 완료', 'worker01'),
('CAPA-20260303-001', 'CORRECTIVE', '작업표준서 WI-W-003 개정', '개정 진행 중', 'mgr01'),
('CAPA-20260303-002', 'ROOT_CAUSE', 'AI 경고 원인 분석 — 온도 상승 추세', NULL, 'mgr01'),
('CAPA-20260303-002', 'PREVENTIVE', '냉각시스템 점검 계획', NULL, 'mgr01'),
('CAPA-20260303-002', 'PREVENTIVE', '온도 모니터링 임계값 조정', NULL, 'admin'),
('CAPA-20260304-001', 'ROOT_CAUSE', '두께 편차 원인 — 프레스 압력 불균일', '확인 완료', 'mgr02'),
('CAPA-20260304-001', 'CORRECTIVE', '프레스 압력 조정', '조정 완료', 'mgr02'),
('CAPA-20260304-001', 'VERIFICATION', '10일간 SPC 모니터링 — Cpk 1.33 이상 확인 중', NULL, 'mgr02'),
('CAPA-20260304-002', 'ROOT_CAUSE', '검사 주기 적정성 분석', '분석 완료', 'worker02'),
('CAPA-20260304-002', 'PREVENTIVE', '공정검사 주기 2시간→1시간 단축', '적용 완료', 'worker02'),
('CAPA-20260304-002', 'VERIFICATION', '품질 지표 개선 여부 모니터링 중', NULL, 'mgr01'),
('CAPA-20260228-001', 'ROOT_CAUSE', '도장 두께 편차 원인 — 스프레이건 노즐 마모', '확인', 'worker01'),
('CAPA-20260228-001', 'CORRECTIVE', '노즐 교환 + 도장 조건 재설정', '완료', 'worker01'),
('CAPA-20260228-001', 'VERIFICATION', 'Cpk 1.52 달성 확인', '합격', 'mgr02'),
('CAPA-20260228-002', 'ROOT_CAUSE', '설비 다운타임 추세 분석', '분석 완료', 'mgr01'),
('CAPA-20260228-002', 'PREVENTIVE', '분기별 예방보전 계획 수립', '수립 완료', 'mgr01'),
('CAPA-20260228-002', 'VERIFICATION', '1분기 보전 계획 실행 확인', '승인 완료', 'admin')
ON CONFLICT DO NOTHING;

-- ─── OEE 일일 집계 (150건: 15개 설비 × 10일) ────────────────
INSERT INTO oee_daily (equip_code, calc_date, planned_time, downtime, ideal_ct, total_count, good_count, availability, performance, quality_rate, oee)
SELECT
    e.equip_code,
    d.dt::date,
    480,
    (random() * 60)::numeric(8,2),
    (60.0 / e.capacity_per_hour)::numeric(8,4),
    (e.capacity_per_hour * 7 + (random() * e.capacity_per_hour)::int),
    (e.capacity_per_hour * 7 + (random() * e.capacity_per_hour)::int - (random() * 20)::int),
    (0.80 + random() * 0.18)::numeric(5,4),
    (0.75 + random() * 0.20)::numeric(5,4),
    (0.90 + random() * 0.09)::numeric(5,4),
    ((0.80 + random() * 0.18) * (0.75 + random() * 0.20) * (0.90 + random() * 0.09))::numeric(5,4)
FROM equipments e
CROSS JOIN generate_series(CURRENT_DATE - INTERVAL '9 days', CURRENT_DATE, INTERVAL '1 day') AS d(dt)
ON CONFLICT DO NOTHING;

-- ─── 알림 (50건: 유형별 10건) ────────────────────────────────
INSERT INTO notifications (user_id, type, title, message, severity) VALUES
('admin', 'EQUIP_DOWN', 'EQP-001 설비 다운', '진동 이상 감지, 즉시 점검 필요', 'CRITICAL'),
('admin', 'EQUIP_DOWN', 'EQP-003 설비 정지', '정기 보전 작업으로 인한 정지', 'INFO'),
('mgr01', 'EQUIP_DOWN', 'EQP-007 비상 정지', '과전류 감지, 안전 차단', 'CRITICAL'),
('mgr01', 'EQUIP_DOWN', 'EQP-010 센서 이상', '온도 센서 불량 의심', 'WARNING'),
('worker01', 'EQUIP_DOWN', 'EQP-005 설비 다운', '모터 과열 감지', 'CRITICAL'),
('admin', 'SPC_VIOLATION', 'ITM-00001 외경 UCL 초과', '연속 2점 2σ 초과', 'WARNING'),
('mgr02', 'SPC_VIOLATION', 'ITM-00002 외경 3σ 초과', '즉시 공정 확인 필요', 'CRITICAL'),
('mgr02', 'SPC_VIOLATION', 'ITM-00004 경도 편차', '연속 8점 한쪽 편향', 'WARNING'),
('worker01', 'SPC_VIOLATION', 'ITM-00005 두께 UCL 초과', '서브그룹 #5에서 위반', 'CRITICAL'),
('admin', 'SPC_VIOLATION', 'ITM-00003 길이 경고', '연속 4점 1σ 초과', 'WARNING'),
('admin', 'INVENTORY_LOW', 'ITM-00006 안전재고 미달', '현재 재고 15/50', 'WARNING'),
('mgr01', 'INVENTORY_LOW', 'ITM-00008 재고 부족', '현재 재고 5/30', 'CRITICAL'),
('mgr01', 'INVENTORY_LOW', 'ITM-00012 원자재 부족', '3일분 미만 재고', 'WARNING'),
('worker01', 'INVENTORY_LOW', 'ITM-00015 안전재고 경고', '현재 재고 22/50', 'INFO'),
('admin', 'INVENTORY_LOW', 'ITM-00003 재고 관리', '입고 예정일 확인 필요', 'INFO'),
('admin', 'AI_WARNING', '수요예측 급증 경고', 'ITM-00001 다음 달 수요 200% 증가 예측', 'WARNING'),
('mgr01', 'AI_WARNING', '불량률 상승 예측', 'EQP-003 라인 불량률 15% 예측', 'CRITICAL'),
('mgr02', 'AI_WARNING', '설비 고장 예측', 'EQP-007 30일 이내 고장 확률 85%', 'CRITICAL'),
('worker01', 'AI_WARNING', '품질 이상 감지', 'ITM-00004 생산 품질 하락 추세', 'WARNING'),
('admin', 'AI_WARNING', '스케줄 최적화 제안', '생산 순서 변경으로 15% 효율 향상 가능', 'INFO'),
('mgr02', 'CAPA_DUE', 'CAPA-20260301-001 기한 임박', '3일 후 마감, 현재 OPEN 상태', 'WARNING'),
('mgr01', 'CAPA_DUE', 'CAPA-20260302-001 기한 경과', '기한 초과, 즉시 완료 필요', 'CRITICAL'),
('worker01', 'CAPA_DUE', 'CAPA-20260303-001 진행 알림', 'ACTION 단계, 기한 D-8', 'INFO'),
('admin', 'CAPA_DUE', 'CAPA-20260304-001 검증 알림', 'VERIFICATION 단계, 기한 D-4', 'INFO'),
('mgr02', 'CAPA_DUE', 'CAPA-20260301-002 기한 알림', '기한 D-16, 계획대로 진행', 'INFO'),
('admin', 'SYSTEM', '시스템 업데이트 완료', 'v6.0 Phase 1 배포 완료', 'INFO'),
('admin', 'SYSTEM', 'DB 백업 완료', '일일 자동 백업 정상 완료', 'INFO'),
('mgr01', 'SYSTEM', '사용자 승인 대기', '신규 사용자 2명 승인 대기 중', 'INFO'),
('mgr02', 'SYSTEM', '보고서 생성 완료', '월간 품질 보고서 자동 생성', 'INFO'),
('worker02', 'SYSTEM', '비밀번호 변경 알림', '90일 경과, 비밀번호 변경 권장', 'WARNING'),
('admin', 'EQUIP_DOWN', 'EQP-012 다운', '유압 라인 누유 감지', 'CRITICAL'),
('mgr01', 'EQUIP_DOWN', 'EQP-002 정지', '자재 부족으로 대기', 'INFO'),
('worker02', 'EQUIP_DOWN', 'EQP-009 이상', '진동값 기준 초과', 'WARNING'),
('admin', 'SPC_VIOLATION', 'ITM-00001 무게 편차', '무게 관리한계 근접', 'INFO'),
('mgr01', 'SPC_VIOLATION', 'ITM-00003 무게 3σ 초과', '긴급 조치 필요', 'CRITICAL'),
('admin', 'INVENTORY_LOW', 'ITM-00010 안전재고 미달', '재고 8/25', 'WARNING'),
('worker01', 'INVENTORY_LOW', 'ITM-00001 원자재 부족', '2일분 미만', 'CRITICAL'),
('admin', 'AI_WARNING', '공정 이상 감지', 'PRC-007 공정 온도 편차 확대', 'WARNING'),
('mgr02', 'AI_WARNING', '품질 트렌드 경고', '주간 불량률 상승 추세', 'WARNING'),
('worker02', 'AI_WARNING', '설비 진단 알림', 'EQP-011 베어링 교체 권장', 'INFO'),
('admin', 'CAPA_DUE', 'CAPA 현황 요약', '미완료 CAPA 8건, 기한 초과 2건', 'WARNING'),
('mgr01', 'CAPA_DUE', 'CAPA-20260304-002 알림', 'VERIFICATION 중, D-18', 'INFO'),
('admin', 'SYSTEM', '인증서 갱신 알림', 'SSL 인증서 30일 후 만료', 'WARNING'),
('mgr02', 'SYSTEM', '디스크 용량 경고', 'DB 디스크 사용률 82%', 'WARNING'),
('admin', 'EQUIP_DOWN', 'EQP-015 정지', '냉각수 온도 이상', 'WARNING'),
('mgr01', 'EQUIP_DOWN', 'EQP-004 운영 재개', '보전 작업 완료, 가동 시작', 'INFO'),
('worker01', 'SPC_VIOLATION', 'ITM-00002 두께 경고', '연속 4점 1σ 초과 감지', 'WARNING'),
('mgr02', 'INVENTORY_LOW', 'ITM-00020 재고 경고', '현재 재고 12/40', 'INFO'),
('admin', 'AI_WARNING', '이상 패턴 감지', '야간 생산 품질 저하 패턴', 'WARNING'),
('worker02', 'SYSTEM', '시스템 점검 예고', '3/10 02:00~04:00 서버 점검', 'INFO')
ON CONFLICT DO NOTHING;

-- ─── 알림 설정 (20건: 사용자별) ─────────────────────────────
INSERT INTO notification_settings (user_id, notification_type, channel, is_enabled) VALUES
('admin', 'EQUIP_DOWN', 'WEB', TRUE),
('admin', 'SPC_VIOLATION', 'WEB', TRUE),
('admin', 'INVENTORY_LOW', 'WEB', TRUE),
('admin', 'AI_WARNING', 'WEB', TRUE),
('admin', 'CAPA_DUE', 'WEB', TRUE),
('admin', 'SYSTEM', 'WEB', TRUE),
('mgr01', 'EQUIP_DOWN', 'WEB', TRUE),
('mgr01', 'SPC_VIOLATION', 'WEB', TRUE),
('mgr01', 'AI_WARNING', 'WEB', TRUE),
('mgr01', 'CAPA_DUE', 'WEB', TRUE),
('mgr02', 'SPC_VIOLATION', 'WEB', TRUE),
('mgr02', 'CAPA_DUE', 'WEB', TRUE),
('mgr02', 'AI_WARNING', 'WEB', TRUE),
('mgr02', 'SYSTEM', 'WEB', FALSE),
('worker01', 'EQUIP_DOWN', 'WEB', TRUE),
('worker01', 'SPC_VIOLATION', 'WEB', TRUE),
('worker01', 'INVENTORY_LOW', 'WEB', FALSE),
('worker01', 'CAPA_DUE', 'WEB', TRUE),
('worker02', 'EQUIP_DOWN', 'WEB', TRUE),
('worker02', 'SYSTEM', 'WEB', TRUE)
ON CONFLICT DO NOTHING;
