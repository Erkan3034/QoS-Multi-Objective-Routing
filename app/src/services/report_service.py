"""
=============================================================================
RAPOR OLUŞTURMA SERVİSİ - PDF ve PNG Export
=============================================================================

MODÜL AÇIKLAMASI:
-----------------
Bu modül, optimizasyon sonuçlarını profesyonel PDF raporlarına dönüştürür.
Kullanıcılar sonuçlarını belgeleyebilir ve paylaşabilir.

OLUŞTURULAN RAPORLAR:
---------------------
1. TEKİL SONUÇ RAPORU (generate_pdf_report):
   - Algoritma bilgileri
   - Ağırlık konfigürasyonu
   - Optimizasyon sonuçları (delay, reliability, cost)
   - Bulunan yol
   - Graf görselleştirmesi (varsa)
   - Yakınsama grafiği (varsa)

2. KARŞILAŞTIRMA RAPORU (generate_comparison_report):
   - Birden fazla algoritmanın sonuçlarını karşılaştırır
   - Tablo formatında metrikler
   - En iyi algoritma vurgusu

KULLANILAN KÜTÜPHANELER:
------------------------
- reportlab: PDF oluşturma
- PIL (Pillow): Görüntü işleme

FONT DESTEĞİ:
-------------
Türkçe karakterler için DejaVu Sans fontu tercih edilir.
Bulunamazsa Helvetica (Türkçe desteği yok) kullanılır.

KULLANIM ÖRNEĞİ:
---------------
    from services.report_service import get_report_service, ReportData
    
    service = get_report_service()
    data = ReportData(
        algorithm_name="Genetic Algorithm",
        source=0, destination=249,
        path=[0, 15, 89, 249],
        ...
    )
    service.generate_pdf_report(data, "rapor.pdf")
"""

# =============================================================================
# KÜTÜPHANE İMPORTLARI
# =============================================================================
import os                 # Dosya sistemi işlemleri
import datetime           # Tarih/saat bilgisi
from typing import Dict, List, Optional, Any  # Tip belirteçleri
from dataclasses import dataclass  # Veri sınıfları


# =============================================================================
# PDF OLUŞTURMA KÜTÜPHANESİ (reportlab)
# =============================================================================
# reportlab yüklü değilse PDF oluşturma devre dışı kalır
try:
    from reportlab.lib import colors                    # Renk tanımları
    from reportlab.lib.pagesizes import A4              # Sayfa boyutu
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # Stiller
    from reportlab.lib.units import cm, mm              # Ölçü birimleri
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT  # Hizalama
    from reportlab.pdfbase import pdfmetrics            # Font yönetimi
    from reportlab.pdfbase.ttfonts import TTFont        # TrueType font desteği
    
    REPORTLAB_AVAILABLE = True  # PDF oluşturma aktif
    
    # =========================================================================
    # TÜRKÇE KARAKTER DESTEĞİ İÇİN FONT KAYDI
    # =========================================================================
    # DejaVu Sans: Türkçe karakterleri (ş, ğ, ü, ö, ı, ç) destekler
    # Farklı işletim sistemlerinde farklı konumlarda bulunabilir
    import sys
    FONT_REGISTERED = False
    FONT_NAME = 'DejaVu'           # Normal font
    FONT_NAME_BOLD = 'DejaVu-Bold' # Kalın font
    
    # İşletim sistemine göre olası font yolları
    font_paths = [
        # Windows
        'C:/Windows/Fonts/DejaVuSans.ttf',
        'C:/Windows/Fonts/arial.ttf',
        # Linux
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/TTF/DejaVuSans.ttf',
        # macOS
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    font_bold_paths = [
        'C:/Windows/Fonts/DejaVuSans-Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    
    # Normal fontu kaydet
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
                FONT_REGISTERED = True
                break
            except Exception:
                continue
    
    # Kalın fontu kaydet
    for font_path in font_bold_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, font_path))
                break
            except Exception:
                continue
    
    # Font bulunamazsa varsayılan kullan (Türkçe desteği yok)
    if not FONT_REGISTERED:
        FONT_NAME = 'Helvetica'
        FONT_NAME_BOLD = 'Helvetica-Bold'
        
except ImportError:
    # reportlab yüklü değil - PDF oluşturma devre dışı
    REPORTLAB_AVAILABLE = False
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'


# =============================================================================
# GÖRÜNTÜ İŞLEME KÜTÜPHANESİ (Pillow)
# =============================================================================
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class ReportData:
    """Rapor için gerekli veriler."""
    algorithm_name: str
    source: int
    destination: int
    path: List[int]
    total_delay: float
    total_reliability: float
    resource_cost: float
    weighted_cost: float
    computation_time_ms: float
    weights: Dict[str, float]
    graph_image_path: Optional[str] = None
    convergence_image_path: Optional[str] = None
    node_count: int = 0
    edge_count: int = 0
    seed_used: Optional[int] = None  # Reproducibility için kullanılan seed


class ReportService:
    """PDF ve PNG rapor oluşturma servisi."""
    
    def __init__(self):
        self.styles = None
        self.font_name = FONT_NAME
        self.font_name_bold = FONT_NAME_BOLD
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Özel stil tanımlamaları."""
        if not REPORTLAB_AVAILABLE:
            return
            
        # Başlık stili
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_name_bold,
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e293b')
        ))
        
        # Alt başlık stili
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontName=self.font_name_bold,
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#334155')
        ))
        
        # Normal metin stili
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            spaceAfter=8,
            textColor=colors.HexColor('#475569')
        ))
    
    def is_available(self) -> bool:
        """PDF oluşturma kütüphanesi mevcut mu?"""
        return REPORTLAB_AVAILABLE
    
    def generate_pdf_report(
        self,
        report_data: ReportData,
        output_path: str
    ) -> bool:
        """
        PDF rapor oluşturur.
        
        Args:
            report_data: Rapor verileri
            output_path: Çıktı dosya yolu
            
        Returns:
            Başarılı ise True
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab kütüphanesi yüklü değil. 'pip install reportlab' ile yükleyin.")
        
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Başlık
            story.append(Paragraph(
                "QoS Routing Optimizasyon Raporu",
                self.styles['CustomTitle']
            ))
            
            # Tarih
            now = datetime.datetime.now()
            story.append(Paragraph(
                f"Oluşturulma Tarihi: {now.strftime('%d.%m.%Y %H:%M')}",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 20))
            
            # Genel Bilgiler
            story.append(Paragraph("Genel Bilgiler", self.styles['CustomHeading']))
            
            info_data = [
                ["Algoritma", report_data.algorithm_name],
                ["Kaynak Düğüm", str(report_data.source)],
                ["Hedef Düğüm", str(report_data.destination)],
                ["Düğüm Sayısı", str(report_data.node_count)],
                ["Kenar Sayısı", str(report_data.edge_count)],
                ["Hesaplama Süresi", f"{report_data.computation_time_ms:.2f} ms"],
                ["Seed (Reproducibility)", str(report_data.seed_used) if report_data.seed_used else "-"],
            ]
            
            info_table = Table(info_data, colWidths=[6*cm, 8*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTNAME', (0, 0), (0, -1), self.font_name_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Ağırlıklar
            story.append(Paragraph("Ağırlık Konfigürasyonu", self.styles['CustomHeading']))
            
            weights_data = [
                ["Metrik", "Ağırlık (%)"],
                ["Gecikme (Delay)", f"{report_data.weights.get('delay', 0) * 100:.1f}%"],
                ["Güvenilirlik (Reliability)", f"{report_data.weights.get('reliability', 0) * 100:.1f}%"],
                ["Kaynak Kullanımı (Resource)", f"{report_data.weights.get('resource', 0) * 100:.1f}%"],
            ]
            
            weights_table = Table(weights_data, colWidths=[7*cm, 7*cm])
            weights_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            story.append(weights_table)
            story.append(Spacer(1, 20))
            
            # Sonuç Metrikleri
            story.append(Paragraph("Optimizasyon Sonuçları", self.styles['CustomHeading']))
            
            results_data = [
                ["Metrik", "Değer"],
                ["Toplam Gecikme", f"{report_data.total_delay:.2f} ms"],
                ["Toplam Güvenilirlik", f"{report_data.total_reliability * 100:.2f}%"],
                ["Kaynak Maliyeti", f"{report_data.resource_cost:.4f}"],
                ["Ağırlıklı Maliyet", f"{report_data.weighted_cost:.4f}"],
                ["Yol Uzunluğu", f"{len(report_data.path)} düğüm"],
            ]
            
            results_table = Table(results_data, colWidths=[7*cm, 7*cm])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#22c55e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            story.append(results_table)
            story.append(Spacer(1, 20))
            
            # Bulunan Yol
            story.append(Paragraph("Bulunan Yol", self.styles['CustomHeading']))
            
            path_str = " → ".join(map(str, report_data.path))
            story.append(Paragraph(
                f"<font color='#1e293b'><b>{path_str}</b></font>",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 20))
            
            # Graf Görüntüsü (varsa)
            if report_data.graph_image_path and os.path.exists(report_data.graph_image_path):
                story.append(Paragraph("Graf Görselleştirmesi", self.styles['CustomHeading']))
                try:
                    img = Image(report_data.graph_image_path)
                    img.drawWidth = 14*cm
                    img.drawHeight = 10*cm
                    story.append(img)
                    story.append(Spacer(1, 20))
                except Exception as e:
                    print(f"Graf görüntüsü eklenemedi: {e}")
            
            # Yakınsama Grafiği (varsa)
            if report_data.convergence_image_path and os.path.exists(report_data.convergence_image_path):
                story.append(Paragraph("Yakınsama Grafiği", self.styles['CustomHeading']))
                try:
                    img = Image(report_data.convergence_image_path)
                    img.drawWidth = 14*cm
                    img.drawHeight = 8*cm
                    story.append(img)
                except Exception as e:
                    print(f"Yakınsama grafiği eklenemedi: {e}")
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph(
                "Bu rapor QoS Routing Optimizer v2.4 tarafından otomatik oluşturulmuştur.",
                self.styles['CustomBody']
            ))
            
            # PDF oluştur
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"PDF oluşturma hatası: {e}")
            raise
    
    def generate_comparison_report(
        self,
        results: List[Dict],
        output_path: str,
        source: int,
        destination: int,
        weights: Dict[str, float]
    ) -> bool:
        """
        Algoritma karşılaştırma raporu oluşturur.
        
        Args:
            results: Algoritma sonuçları listesi
            output_path: Çıktı dosya yolu
            source: Kaynak düğüm
            destination: Hedef düğüm
            weights: Ağırlıklar
            
        Returns:
            Başarılı ise True
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab kütüphanesi yüklü değil.")
        
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Başlık
            story.append(Paragraph(
                "Algoritma Karşılaştırma Raporu",
                self.styles['CustomTitle']
            ))
            
            # Tarih
            now = datetime.datetime.now()
            story.append(Paragraph(
                f"Oluşturulma Tarihi: {now.strftime('%d.%m.%Y %H:%M')}",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 20))
            
            # Test Bilgileri
            story.append(Paragraph("Test Parametreleri", self.styles['CustomHeading']))
            story.append(Paragraph(
                f"Kaynak: {source} → Hedef: {destination}",
                self.styles['CustomBody']
            ))
            story.append(Paragraph(
                f"Ağırlıklar: Delay={weights.get('delay', 0):.2f}, "
                f"Reliability={weights.get('reliability', 0):.2f}, "
                f"Resource={weights.get('resource', 0):.2f}",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 20))
            
            # Karşılaştırma Tablosu
            story.append(Paragraph("Sonuç Karşılaştırması", self.styles['CustomHeading']))
            
            table_data = [
                ["Algoritma", "Gecikme (ms)", "Güvenilirlik (%)", "Maliyet", "Süre (ms)"]
            ]
            
            for r in results:
                table_data.append([
                    r.get('algorithm', 'N/A'),
                    f"{r.get('total_delay', 0):.2f}",
                    f"{r.get('total_reliability', 0) * 100:.2f}",
                    f"{r.get('weighted_cost', 0):.4f}",
                    f"{r.get('computation_time_ms', 0):.2f}"
                ])
            
            comparison_table = Table(table_data, colWidths=[3.5*cm, 3*cm, 3.5*cm, 2.5*cm, 2.5*cm])
            comparison_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            story.append(comparison_table)
            story.append(Spacer(1, 20))
            
            # En iyi algoritma
            best = min(results, key=lambda x: x.get('weighted_cost', float('inf')))
            story.append(Paragraph(
                f"<b>En İyi Sonuç:</b> {best.get('algorithm', 'N/A')} "
                f"(Maliyet: {best.get('weighted_cost', 0):.4f})",
                self.styles['CustomBody']
            ))
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph(
                "Bu rapor QoS Routing Optimizer v2.4 tarafından otomatik oluşturulmuştur.",
                self.styles['CustomBody']
            ))
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"PDF oluşturma hatası: {e}")
            raise


# Singleton instance
_report_service = None

def get_report_service() -> ReportService:
    """Singleton ReportService instance döndürür."""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service


__all__ = ['ReportService', 'ReportData', 'get_report_service', 'REPORTLAB_AVAILABLE']
