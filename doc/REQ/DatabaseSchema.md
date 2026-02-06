|     테이블명     |       컬럼명      |      타입     | PK |        FK        | NULL |         설명        |
|:----------------:|:-----------------:|:-------------:|:--:|:----------------:|:----:|:-------------------:|
|       users      |      user_id      |  VARCHAR(50)  |  O |                  |   N  |       사용자ID      |
|       users      |      password     |  VARCHAR(255) |    |                  |   N  |   암호화된비밀번호  |
|       users      |        name       |  VARCHAR(100) |    |                  |   N  |         이름        |
|       users      |        role       |      ENUM     |    |                  |   N  | admin/worker/viewer |
|       users      |     created_at    |    DATETIME   |    |                  |   N  |       생성일시      |
|                  |                   |               |    |                  |      |                     |
|       items      |     item_code     |  VARCHAR(20)  |  O |                  |   N  | 품목코드(ITM-00001) |
|       items      |        name       |  VARCHAR(200) |    |                  |   N  |        품목명       |
|       items      |      category     |      ENUM     |    |                  |   N  |   RAW/SEMI/PRODUCT  |
|       items      |        unit       |  VARCHAR(10)  |    |                  |   N  |      EA/KG/M 등     |
|       items      |        spec       |  VARCHAR(500) |    |                  |   Y  |         규격        |
|       items      |    safety_stock   |      INT      |    |                  |   N  |       안전재고      |
|                  |                   |               |    |                  |      |                     |
|        bom       |       bom_id      |      INT      |  O |                  |   N  |    BOM ID (AUTO)    |
|        bom       |    parent_item    |  VARCHAR(20)  |    |       items      |   N  |        모품목       |
|        bom       |     child_item    |  VARCHAR(20)  |    |       items      |   N  |        자품목       |
|        bom       |    qty_per_unit   | DECIMAL(10,4) |    |                  |   N  |        소요량       |
|        bom       |     loss_rate     |  DECIMAL(5,2) |    |                  |   N  |      로스율(%)      |
|                  |                   |               |    |                  |      |                     |
|     processes    |    process_code   |  VARCHAR(20)  |  O |                  |   N  |       공정코드      |
|     processes    |        name       |  VARCHAR(100) |    |                  |   N  |        공정명       |
|     processes    |    std_time_min   |      INT      |    |                  |   N  |   표준작업시간(분)  |
|     processes    |     equip_code    |  VARCHAR(20)  |    |    equipments    |   Y  |       기본설비      |
|                  |                   |               |    |                  |      |                     |
|    equipments    |     equip_code    |  VARCHAR(20)  |  O |                  |   N  |       설비코드      |
|    equipments    |        name       |  VARCHAR(100) |    |                  |   N  |        설비명       |
|    equipments    |    process_code   |  VARCHAR(20)  |    |     processes    |   N  |       담당공정      |
|    equipments    | capacity_per_hour |      INT      |    |                  |   N  |    시간당생산능력   |
|    equipments    |       status      |      ENUM     |    |                  |   N  |  RUNNING/STOP/DOWN  |
|                  |                   |               |    |                  |      |                     |
| production_plans |      plan_id      |      INT      |  O |                  |   N  |     계획ID(AUTO)    |
| production_plans |     item_code     |  VARCHAR(20)  |    |       items      |   N  |         품목        |
| production_plans |      plan_qty     |      INT      |    |                  |   N  |       계획수량      |
| production_plans |      due_date     |      DATE     |    |                  |   N  |        납기일       |
| production_plans |       status      |      ENUM     |    |                  |   N  |  WAIT/PROGRESS/DONE |
|                  |                   |               |    |                  |      |                     |
|    work_orders   |       wo_id       |  VARCHAR(20)  |  O |                  |   N  |     작업지시번호    |
|    work_orders   |      plan_id      |      INT      |    | production_plans |   N  |       생산계획      |
|    work_orders   |     work_date     |      DATE     |    |                  |   N  |        작업일       |
|    work_orders   |     equip_code    |  VARCHAR(20)  |    |    equipments    |   N  |         설비        |
|    work_orders   |      plan_qty     |      INT      |    |                  |   N  |       지시수량      |
|    work_orders   |       status      |      ENUM     |    |                  |   N  |  WAIT/WORKING/DONE  |
|                  |                   |               |    |                  |      |                     |
|   work_results   |     result_id     |      INT      |  O |                  |   N  |     실적ID(AUTO)    |
|   work_results   |       wo_id       |  VARCHAR(20)  |    |    work_orders   |   N  |       작업지시      |
|   work_results   |      good_qty     |      INT      |    |                  |   N  |       양품수량      |
|   work_results   |     defect_qty    |      INT      |    |                  |   N  |       불량수량      |
|   work_results   |     worker_id     |  VARCHAR(50)  |    |       users      |   N  |        작업자       |
|   work_results   |     start_time    |    DATETIME   |    |                  |   N  |       시작시간      |
|   work_results   |      end_time     |    DATETIME   |    |                  |   N  |       종료시간      |
|                  |                   |               |    |                  |      |                     |
|     inventory    |       inv_id      |      INT      |  O |                  |   N  |     재고ID(AUTO)    |
|     inventory    |     item_code     |  VARCHAR(20)  |    |       items      |   N  |         품목        |
|     inventory    |       lot_no      |  VARCHAR(30)  |    |                  |   N  |       로트번호      |
|     inventory    |        qty        |      INT      |    |                  |   N  |         수량        |
|     inventory    |     warehouse     |  VARCHAR(10)  |    |                  |   N  |         창고        |
|     inventory    |      location     |  VARCHAR(20)  |    |                  |   Y  |    위치(A-01-01)    |
