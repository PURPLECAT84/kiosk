import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('ko', null);
  runApp(const KioskApp());
}

class KioskApp extends StatelessWidget {
  const KioskApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MOKI Senior Kiosk',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xff7C3AED),
          primary: const Color(0xff7C3AED),
          background: const Color(0xffF3F4F6),
        ),
        fontFamily: 'Roboto',
      ),
      home: const KioskHomeScreen(),
    );
  }
}

// 가상 키오스크 상태 설정
const String defaultKioskId = "88888888-8888-8888-8888-888888888888"; // 로컬 시뮬레이션용 ID
const String backendUrl = "http://127.0.0.1:8000"; // 로컬 FastAPI 백엔드 주소

class CartItem {
  final String productId;
  final String name;
  final int price;
  int quantity;

  CartItem({
    required this.productId,
    required this.name,
    required this.price,
    this.quantity = 1,
  });
}

class KioskHomeScreen extends StatefulWidget {
  const KioskHomeScreen({super.key});

  @override
  State<KioskHomeScreen> createState() => _KioskHomeScreenState();
}

class _KioskHomeScreenState extends State<KioskHomeScreen> {
  // 실시간 시계용
  late Timer _clockTimer;
  String _currentTime = "";

  // API 동기화 데이터
  String _storeName = "모두의 키오스크";
  String _kioskType = "Restaurant"; // 기본형: 외식형(Restaurant)
  String _storeId = "";
  List<dynamic> _categories = [];
  int _selectedCategoryIndex = 0;
  bool _isLoading = true;
  String _errorMessage = "";

  // 장바구니 상태
  final List<CartItem> _cart = [];

  @override
  void initState() {
    super.initState();
    _updateTime();
    _clockTimer = Timer.periodic(const Duration(seconds: 1), (timer) => _updateTime());
    _syncKioskData();
  }

  @override
  void dispose() {
    _clockTimer.cancel();
    super.dispose();
  }

  void _updateTime() {
    final DateTime now = DateTime.now();
    final String formattedTime = DateFormat('yyyy.MM.dd (E) HH:mm:ss', 'ko').format(now);
    setState(() {
      _currentTime = formattedTime;
    });
  }

  // 백엔드 API로부터 상품 및 매장 타입 동기화
  Future<void> _syncKioskData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = "";
    });

    try {
      // 1. 키오스크 상세 조회하여 store_id 및 type 확인
      final kioskRes = await http.get(Uri.parse('$backendUrl/kiosks/$defaultKioskId'));
      if (kioskRes.statusCode == 200) {
        final kioskData = json.decode(kioskRes.body);
        _kioskType = kioskData['type'] ?? 'Restaurant';
        _storeId = kioskData['store_id'];
      }

      // 2. 카테고리 & 상품 리스트 동기화
      final syncRes = await http.get(Uri.parse('$backendUrl/kiosk_client/sync/$defaultKioskId'));
      if (syncRes.statusCode == 200) {
        final syncData = json.decode(syncRes.body);
        setState(() {
          _storeName = syncData['store_name'];
          _categories = syncData['categories'];
          _isLoading = false;
        });
      } else {
        throw Exception("동기화 API 호출 실패");
      }
    } catch (e) {
      // API 연결 실패 시 오프라인 모드용 더미 데이터 폴백
      setState(() {
        _storeName = "모키 반점 (오프라인 모드)";
        _kioskType = "Restaurant";
        _categories = _getOfflineDummyData();
        _isLoading = false;
      });
    }
  }

  // 오프라인 가동용 더미 데이터
  List<dynamic> _getOfflineDummyData() {
    return [
      {
        "id": 1,
        "name": "🔥 추천 요리",
        "sequence": 1,
        "products": [
          {"id": "p1", "name": "명품 짜장면", "price": 7000, "image": "", "stock": 50, "status": "ACTIVE", "sequence": 1},
          {"id": "p2", "name": "해물 짬뽕", "price": 8500, "image": "", "stock": 20, "status": "ACTIVE", "sequence": 2},
          {"id": "p3", "name": "찹쌀 탕수육 (소)", "price": 15000, "image": "", "stock": 10, "status": "ACTIVE", "sequence": 3},
          {"id": "p4", "name": "군만두 (8개)", "price": 6000, "image": "", "stock": 0, "status": "SOLDOUT", "sequence": 4},
        ]
      },
      {
        "id": 2,
        "name": "🍚 식사류",
        "sequence": 2,
        "products": [
          {"id": "p5", "name": "볶음밥", "price": 8000, "image": "", "stock": 30, "status": "ACTIVE", "sequence": 1},
          {"id": "p6", "name": "잡채밥", "price": 9000, "image": "", "stock": 15, "status": "ACTIVE", "sequence": 2},
        ]
      },
      {
        "id": 3,
        "name": "🥤 음료/주류",
        "sequence": 3,
        "products": [
          {"id": "p7", "name": "콜라", "price": 2000, "image": "", "stock": 100, "status": "ACTIVE", "sequence": 1},
          {"id": "p8", "name": "사이다", "price": 2000, "image": "", "stock": 100, "status": "ACTIVE", "sequence": 2},
        ]
      }
    ];
  }

  // 장바구니에 상품 담기
  void _addToCart(dynamic product) {
    if (product['status'] == 'SOLDOUT') {
      _showAlertDialog("품절된 상품입니다", "재고가 부족하여 주문할 수 없습니다.");
      return;
    }
    
    setState(() {
      final existingIndex = _cart.indexWhere((item) => item.productId == product['id']);
      if (existingIndex >= 0) {
        _cart[existingIndex].quantity += 1;
      } else {
        _cart.add(CartItem(
          productId: product['id'],
          name: product['name'],
          price: product['price'],
        ));
      }
    });
  }

  // 수량 가감
  void _updateCartItemQuantity(int index, int delta) {
    setState(() {
      _cart[index].quantity += delta;
      if (_cart[index].quantity <= 0) {
        _cart.removeAt(index);
      }
    });
  }

  int _getCartTotal() {
    return _cart.fold(0, (sum, item) => sum + (item.price * item.quantity));
  }

  // 알림 다이얼로그
  void _showAlertDialog(String title, String message) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 24)),
        content: Text(message, style: const TextStyle(fontSize: 18)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text("확인", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          )
        ],
      ),
    );
  }

  // 결제하기 클릭 액션
  void _handlePaymentPress() {
    if (_cart.isEmpty) {
      _showAlertDialog("장바구니가 비어 있습니다", "주문하실 상품을 먼저 선택해 주세요.");
      return;
    }

    if (_kioskType == "Restaurant") {
      // 외식형 -> 휴대폰 번호 입력 전체 화면 노출
      _showPhoneInputScreen();
    } else {
      // 일반 판매형 -> 즉시 가상 결제 프로세스
      _runVirtualPaymentProcess(null);
    }
  }

  // 휴대폰 번호 입력 전체화면 팝업
  void _showPhoneInputScreen() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => const PhoneInputBottomSheet(),
    ).then((phoneNumber) {
      if (phoneNumber != null && phoneNumber is String && phoneNumber.isNotEmpty) {
        // 전화번호 입력 완료 시 결제 프로세스로 전송
        _runVirtualPaymentProcess(phoneNumber);
      }
    });
  }

  // 가상 결제 로딩 애니메이션 및 Mock API 호출
  void _runVirtualPaymentProcess(String? phoneNumber) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const VirtualCardPaymentDialog(),
    );

    // 3초간 가상 카드 로딩 애니메이션 연출 후 결제 API 호출
    Timer(const Duration(seconds: 3), () async {
      Navigator.of(context).pop(); // 결제 진행 모달 닫기
      
      try {
        // Mock 결제 페이로드 빌드
        final List<Map<String, dynamic>> itemsPayload = _cart.map((item) => {
          "product_id": item.productId,
          "quantity": item.quantity,
        }).toList();

        final res = await http.post(
          Uri.parse('$backendUrl/kiosk_client/pay/mock'),
          headers: {"Content-Type": "application/json"},
          body: json.encode({
            "store_id": _storeId.isNotEmpty ? _storeId : "88888888-8888-8888-8888-888888888888",
            "total_amount": _getCartTotal(),
            "payment_method": "카드",
            "order_no": phoneNumber,
            "items": itemsPayload
          }),
        );

        if (res.statusCode == 200) {
          final data = json.decode(res.body);
          _showPaymentSuccessDialog(data['order_no'], data['approval_code']);
        } else {
          final errorData = json.decode(res.body);
          _showAlertDialog("결제 실패", errorData['detail'] ?? "결제 처리 중 서버 에러가 발생했습니다.");
        }
      } catch (e) {
        // 백엔드 연결 불가 시에도 강제 가상 결제 성공 처리 (Kiosk UX 보장)
        final String formattedDate = DateFormat('yyMMdd').format(DateTime.now());
        final String approvalCode = formattedDate + "123456";
        final String orderNo = phoneNumber ?? (formattedDate + "654321");
        _showPaymentSuccessDialog(orderNo, approvalCode);
      }
    });
  }

  // 결제 완료 안내 다이얼로그
  void _showPaymentSuccessDialog(String orderNo, String approvalCode) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
        content: Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.check_circle, color: Color(0xff7C3AED), size: 100),
              const SizedBox(height: 24),
              const Text("결제 완료!", style: TextStyle(fontSize: 36, fontWeight: FontWeight.w800, color: Colors.black)),
              const SizedBox(height: 16),
              const Text("카드를 회수하고 영수증을 확인해 주세요.", style: TextStyle(fontSize: 20, color: Colors.grey, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
              const Divider(height: 40),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("주문 번호", style: TextStyle(fontSize: 18, color: Colors.grey, fontWeight: FontWeight.bold)),
                  Text(orderNo, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xff7C3AED))),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("승인 번호", style: TextStyle(fontSize: 18, color: Colors.grey, fontWeight: FontWeight.bold)),
                  Text(approvalCode, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () {
                  Navigator.of(ctx).pop();
                  setState(() {
                    _cart.clear(); // 장바구니 초기화
                  });
                  _syncKioskData(); // 재고 상태 동기화 재수행
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xff7C3AED),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: const Text("처음으로 돌아가기", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              )
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xffF3F4F6),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            // FHD 세로형 규격(1080x1920) 타겟팅 비율 기반 동적 레이아웃 분할
            final double screenHeight = constraints.maxHeight;
            final double headerHeight = screenHeight * 0.15;
            final double bodyHeight = screenHeight * 0.60;
            final double footerHeight = screenHeight * 0.25;

            return Column(
              children: [
                // 1. 상단 (15%): 매장명, 시간, 안내문구
                Container(
                  height: headerHeight,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            _storeName,
                            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: Color(0xff7C3AED)),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            "원하시는 메뉴를 터치하여 담아주세요.",
                            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.grey),
                          )
                        ],
                      ),
                      // 시계
                      Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            _currentTime,
                            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.black87, fontFamily: 'monospace'),
                          ),
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            decoration: BoxDecoration(
                              color: const Color(0xff7C3AED).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _kioskType == "Restaurant" ? "외식형 KIOSK" : "상품판매형 KIOSK",
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xff7C3AED)),
                            ),
                          )
                        ],
                      )
                    ],
                  ),
                ),

                // 2. 중앙 (60%): 카테고리 + 상품 목록
                Container(
                  height: bodyHeight,
                  child: Row(
                    children: [
                      // 좌측: 카테고리 탭 (25% 너비)
                      Container(
                        width: constraints.maxWidth * 0.25,
                        decoration: const BoxDecoration(
                          color: Colors.white,
                          border: Border(right: BorderSide(color: Color(0xffE5E7EB), width: 1.5)),
                        ),
                        child: ListView.builder(
                          itemCount: _categories.length,
                          itemBuilder: (context, index) {
                            final cat = _categories[index];
                            final isSelected = index == _selectedCategoryIndex;
                            return InkWell(
                              onTap: () {
                                setState(() {
                                  _selectedCategoryIndex = index;
                                });
                              },
                              child: Container(
                                height: 96, // 터치 타겟 64dp 이상 확보
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  color: isSelected ? const Color(0xff7C3AED).withOpacity(0.08) : Colors.white,
                                  border: Border(
                                    left: BorderSide(
                                      color: isSelected ? const Color(0xff7C3AED) : Colors.transparent,
                                      width: 6,
                                    ),
                                    bottom: const BorderSide(color: Color(0xffF3F4F6)),
                                  ),
                                ),
                                child: Text(
                                  cat['name'],
                                  style: TextStyle(
                                    fontSize: 22,
                                    fontWeight: isSelected ? FontWeight.w800 : FontWeight.bold,
                                    color: isSelected ? const Color(0xff7C3AED) : Colors.black87,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            );
                          },
                        ),
                      ),

                      // 우측: 상품 그리드 뷰 (75% 너비)
                      Expanded(
                        child: _isLoading
                            ? const Center(child: Loader2(animate: true))
                            : _categories.isEmpty
                                ? const Center(child: Text("등록된 상품 카테고리가 없습니다.", style: TextStyle(fontSize: 20)))
                                : GridView.builder(
                                    padding: const EdgeInsets.all(24),
                                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                      crossAxisCount: 2, // 시니어를 위한 2열 배치 극대화
                                      childAspectRatio: 0.82,
                                      crossAxisSpacing: 20,
                                      mainAxisSpacing: 20,
                                    ),
                                    itemCount: _categories[_selectedCategoryIndex]['products'].length,
                                    itemBuilder: (context, index) {
                                      final product = _categories[_selectedCategoryIndex]['products'][index];
                                      final isSoldOut = product['status'] == 'SOLDOUT';

                                      return InkWell(
                                        onTap: () => _addToCart(product),
                                        splashColor: const Color(0xff7C3AED).withOpacity(0.2), // 보라색 리플 효과
                                        borderRadius: BorderRadius.circular(24),
                                        child: Card(
                                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                                          color: Colors.white,
                                          elevation: 2,
                                          child: Stack(
                                            children: [
                                              Padding(
                                                padding: const EdgeInsets.all(16.0),
                                                child: Column(
                                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                                  children: [
                                                    // 상품 이미지 플레이스홀더 (그레이 박스)
                                                    Expanded(
                                                      child: ClipRRect(
                                                        borderRadius: BorderRadius.circular(16),
                                                        child: product['image'] != null && product['image'].toString().isNotEmpty
                                                            ? Image.network(
                                                                product['image'].toString().startsWith('http')
                                                                    ? product['image'].toString()
                                                                    : '$backendUrl${product['image']}',
                                                                fit: BoxFit.cover,
                                                                errorBuilder: (context, error, stackTrace) {
                                                                  return Container(
                                                                    color: const Color(0xffF3F4F6),
                                                                    child: const Icon(
                                                                      Icons.fastfood,
                                                                      color: Colors.grey,
                                                                      size: 54,
                                                                    ),
                                                                  );
                                                                },
                                                              )
                                                            : Container(
                                                                color: const Color(0xffF3F4F6),
                                                                child: const Icon(
                                                                  Icons.fastfood,
                                                                  color: Colors.grey,
                                                                  size: 54,
                                                                ),
                                                              ),
                                                      ),
                                                    ),
                                                    const SizedBox(height: 12),
                                                    Text(
                                                      product['name'],
                                                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: Colors.black),
                                                      maxLines: 1,
                                                      overflow: TextOverflow.ellipsis,
                                                    ),
                                                    const SizedBox(height: 6),
                                                    Text(
                                                      "₩${product['price'].toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}",
                                                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: Color(0xff7C3AED)),
                                                    )
                                                  ],
                                                ),
                                              ),
                                              // 품절 오버레이
                                              if (isSoldOut)
                                                Container(
                                                  decoration: BoxDecoration(
                                                    color: Colors.black.withOpacity(0.6),
                                                    borderRadius: BorderRadius.circular(24),
                                                  ),
                                                  child: const Center(
                                                    child: Text(
                                                      "품 절",
                                                      style: TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w800, letterSpacing: 4),
                                                    ),
                                                  ),
                                                )
                                            ],
                                          ),
                                        ),
                                      );
                                    },
                                  ),
                      ),
                    ],
                  ),
                ),

                // 3. 하단 (25%): 장바구니 + 총액 + 결제하기
                Container(
                  height: footerHeight,
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    border: Border(top: BorderSide(color: Color(0xffE5E7EB), width: 2)),
                  ),
                  child: Row(
                    children: [
                      // 장바구니 품목 (좌측 70%)
                      Expanded(
                        child: _cart.isEmpty
                            ? const Center(
                                child: Text(
                                  "선택하신 메뉴가 없습니다. 위의 메뉴판을 터치해 주세요. 🛒",
                                  style: TextStyle(fontSize: 18, color: Colors.grey, fontWeight: FontWeight.bold),
                                ),
                              )
                            : ListView.builder(
                                scrollDirection: Axis.horizontal,
                                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                                itemCount: _cart.length,
                                itemBuilder: (context, index) {
                                  final item = _cart[index];
                                  return Container(
                                    width: 200,
                                    margin: const EdgeInsets.only(right: 16),
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: const Color(0xffF3F4F6),
                                      borderRadius: BorderRadius.circular(16),
                                      border: Border.all(color: const Color(0xffE5E7EB)),
                                    ),
                                    child: Column(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          item.name,
                                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                        Text(
                                          "₩${(item.price * item.quantity).toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}",
                                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xff7C3AED)),
                                        ),
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            IconButton(
                                              onPressed: () => _updateCartItemQuantity(index, -1),
                                              icon: const Icon(Icons.remove_circle, color: Colors.red, size: 28),
                                              padding: EdgeInsets.zero,
                                              constraints: const BoxConstraints(),
                                            ),
                                            Text(
                                              "${item.quantity}개",
                                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                                            ),
                                            IconButton(
                                              onPressed: () => _updateCartItemQuantity(index, 1),
                                              icon: const Icon(Icons.add_circle, color: Color(0xff7C3AED), size: 28),
                                              padding: EdgeInsets.zero,
                                              constraints: const BoxConstraints(),
                                            ),
                                          ],
                                        )
                                      ],
                                    ),
                                  );
                                },
                              ),
                      ),
                      
                      // 총금액 및 결제버튼 (우측 30%)
                      Container(
                        width: constraints.maxWidth * 0.32,
                        padding: const EdgeInsets.all(20),
                        decoration: const BoxDecoration(
                          border: Border(left: BorderSide(color: Color(0xffE5E7EB), width: 1.5)),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text("선택 총액", style: TextStyle(fontSize: 18, color: Colors.grey, fontWeight: FontWeight.bold)),
                                Text(
                                  "₩${_getCartTotal().toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}",
                                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Colors.black),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            ElevatedButton(
                              onPressed: _handlePaymentPress,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xff7C3AED),
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(vertical: 20),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                                elevation: 3,
                              ),
                              child: const Text(
                                "결제하기",
                                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: 2),
                              ),
                            )
                          ],
                        ),
                      )
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

// 로더 애니메이션 보조 위젯
class Loader2 extends StatelessWidget {
  final bool animate;
  const Loader2({super.key, required this.animate});

  @override
  Widget build(BuildContext context) {
    return const Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        CircularProgressIndicator(color: Color(0xff7C3AED), strokeWidth: 5),
        SizedBox(height: 16),
        Text("메뉴 데이터를 불러오는 중...", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey)),
      ],
    );
  }
}

// 가상 카드 리더 로딩 팝업
class VirtualCardPaymentDialog extends StatelessWidget {
  const VirtualCardPaymentDialog({super.key});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: Color(0xff7C3AED), strokeWidth: 6),
            const SizedBox(height: 32),
            const Text(
              "IC 카드를 끝까지 넣어주세요",
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.black),
            ),
            const SizedBox(height: 12),
            Text(
              "승인이 완료될 때까지 카드를 빼지 마세요.",
              style: TextStyle(fontSize: 16, color: Colors.grey[600], fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.amber[50],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.amber[200]!),
              ),
              child: const Row(
                children: [
                  Icon(Icons.warning, color: Colors.amber),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      "가상 결제 테스트 진행 중입니다. (결제금액은 실제로 청구되지 않습니다)",
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.amber),
                    ),
                  )
                ],
              ),
            )
          ],
        ),
      ),
    );
  }
}

// 휴대폰 번호 입력 전체 화면 바텀시트
class PhoneInputBottomSheet extends StatefulWidget {
  const PhoneInputBottomSheet({super.key});

  @override
  State<PhoneInputBottomSheet> createState() => _PhoneInputBottomSheetState();
}

class _PhoneInputBottomSheetState extends State<PhoneInputBottomSheet> {
  String _phoneNumber = "010";

  void _onKeyPress(String value) {
    setState(() {
      if (value == "BACK") {
        if (_phoneNumber.length > 3) {
          _phoneNumber = _phoneNumber.substring(0, _phoneNumber.length - 1);
        }
      } else {
        if (_phoneNumber.length < 11) {
          _phoneNumber += value;
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(36),
          topRight: Radius.circular(36),
        ),
      ),
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("주문서 발송 연락처 입력", style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
              IconButton(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.close, size: 36),
              )
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            "카카오톡으로 주문서 및 영수증을 받아보실 휴대폰 번호를 입력해 주세요.",
            style: TextStyle(fontSize: 18, color: Colors.grey, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 32),
          // 번호 노출창
          Container(
            padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
            decoration: BoxDecoration(
              color: const Color(0xffF3F4F6),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xffE5E7EB), width: 2),
            ),
            alignment: Alignment.center,
            child: Text(
              _phoneNumber,
              style: const TextStyle(fontSize: 48, fontWeight: FontWeight.w800, color: Color(0xff7C3AED), letterSpacing: 4),
            ),
          ),
          const SizedBox(height: 32),
          // 대형 터치 키패드 (시니어 고려 최소 크기 확보)
          Expanded(
            child: GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 1.5,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
              ),
              itemCount: 12,
              itemBuilder: (ctx, idx) {
                String keyLabel = "";
                if (idx < 9) {
                  keyLabel = (idx + 1).toString();
                } else if (idx == 9) {
                  keyLabel = "지우기";
                } else if (idx == 10) {
                  keyLabel = "0";
                } else if (idx == 11) {
                  keyLabel = "BACK"; // 아이콘 대체용
                }

                final isBack = keyLabel == "BACK";
                final isClear = keyLabel == "지우기";

                return ElevatedButton(
                  onPressed: () {
                    if (isClear) {
                      setState(() {
                        _phoneNumber = "010";
                      });
                    } else if (isBack) {
                      _onKeyPress("BACK");
                    } else {
                      _onKeyPress(keyLabel);
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isClear || isBack ? Colors.grey[200] : const Color(0xffF3F4F6),
                    foregroundColor: Colors.black87,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: isBack 
                    ? const Icon(Icons.backspace, size: 28, color: Colors.red)
                    : Text(
                        keyLabel,
                        style: TextStyle(
                          fontSize: isClear ? 20 : 32,
                          fontWeight: FontWeight.bold,
                          color: isClear ? Colors.red : Colors.black87
                        ),
                      ),
                );
              },
            ),
          ),
          const SizedBox(height: 24),
          // 다음(결제진행) 버튼
          ElevatedButton(
            onPressed: _phoneNumber.length >= 10
                ? () => Navigator.of(context).pop(_phoneNumber)
                : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xff7C3AED),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 22),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              disabledBackgroundColor: Colors.grey[300],
            ),
            child: const Text("입력 완료 및 카드결제", style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
          )
        ],
      ),
    );
  }
}

