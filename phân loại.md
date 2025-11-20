1 : phân loại sản phẩm
- Vacuum Cleaner : 
    + AZ3002
    + IX141
    + IZ381H
    + LA480
    + LA555
    + LA700
    + LA800
    + NV360
    + SV2000
    + UV440
    + UV730
    + ZD201
    + ZU660
- Wet Cleaner : 
    + AW261
    + WD161
- Wet & Dry : 
    + VX100
    + VS100
    + HX100
- Air Purifier : 
    + HP152
    + HP301
    + UA1450
- Fan
    + FA225
    + TF200
    + UH205
- Hair Dryer : 
    + HD300
    + HD400
    + HD500
    + HD600
    + HD700
2 : Thêm hình cho từng sản phẩm : 
replit-po\web\templates\index.html
replit-po\web\templates\batch.html
- Vacuum Cleaner : 
    + AZ3002 ->    AZ3002_01.avif
    + IX141  ->    IX141H_01.avif
    + IZ381H  ->   IZ382H_mobileLarge_02.avif
    + LA480 ->     la486.avif
    + LA555 ->     la555.jpg
    + LA700 ->     la700.jpg
    + LA800 ->     LA802_mobileLarge_01.avif
    + NV360 ->     NV360_01.avif
    + SV2000 ->    SV2000.avif
    + UV440 ->     uv440.jpeg
    + UV730 ->     uv730.jpg
    + ZD201 ->     zd201.jpg
    + ZU660 ->     zd660.webp
- Wet Cleaner : 
    + AW261 ->     aw261.jpg
    + WD161 ->     wd161.jpg
- Wet & Dry : 
    + VX100 ->     vx100.jpg
    + VS100 ->     vs100.jpeg
    + HX100 ->     hx100.webp
- Air Purifier : 
    + HP152  ->    HP152_01.avif
    + HP301 ->     HP301_01.avif
    + UA1450 ->    UA1450_01.avif
- Fan
    + FA225 ->     FA202_02.avif
    + TF200 ->     TF200-ATF-01B.webp
    + UH205 ->     uh205.webp
- Hair Dryer : 
    + HD300 ->     hd300.jpg
    + HD400 ->     HD400BKSN_02.avif
    + HD500 ->     HD500_02.avif
    + HD600 ->     hd600.jpg
    + HD700 ->     HD700_02.avif
3 : Thêm vào sidebar những tính năng còn thiếu : 
    + Quản lý người dùng @user.html
    + Bulk Operation @bulk
4 : Sửa <!-- Type Badge --> cho tất cả sản phẩm dựa trên loại sản phẩm
5 : Ở <!-- Card Body -->  thay " Product Template " thành : 
    Đối với các sản phẩm thuộc : 
    +Vacuum Cleaner :  Performance Nozzle vs Hose - Hard floor, Speed
    +Wet Cleaner : Performance, water flow, speed
    +Wet & Dry : Performance Nozzle vs Hose - Hard floor, Speed
    +Air Purifier : Speed, Power draw, Sensor filter
    +Fan : Air flow, Speed, Power
    +Hair Dryer : Air Flow, Power 
    Code ví dụ : 
    <div class="flex flex-1 flex-col p-4">
                            <div class="mb-4">
                                <h3 class="text-lg font-semibold text-slate-200">ZU660</h3>
                                <p class="text-sm text-slate-500">Performance Nozzle vs Hose - Hard floor, Speed</p>
                            </div>

                            <div class="mt-auto flex gap-2">
                                <button onclick="openProduct('ZU660')" class="flex-1 rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-white transition-colors add-to-cart-btn">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" data-lucide="file-edit" class="lucide lucide-file-edit mr-2 h-4 w-4 inline-block"><path d="M12.659 22H18a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v9.34"></path><path d="M14 2v5a1 1 0 0 0 1 1h5"></path><path d="M10.378 12.622a1 1 0 0 1 3 3.003L8.36 20.637a2 2 0 0 1-.854.506l-2.867.837a.5.5 0 0 1-.62-.62l.836-2.869a2 2 0 0 1 .506-.853z"></path></svg> Tạo File
                                </button>
                                <button onclick="viewProductInfo('ZU660')" class="flex items-center justify-center rounded-lg border border-slate-700 bg-transparent px-3 py-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" data-lucide="info" class="lucide lucide-info h-4 w-4"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
                                </button>
                            </div>
                        </div>