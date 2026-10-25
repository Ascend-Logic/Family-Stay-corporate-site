// 役員写真（正方形 700x700）から、経営陣カード用の横長写真（1330x700 = 1.9:1）を作る。
// 人物だけを切り抜き、単色の背景（#EDEDE9。役員写真の背景グラデーションの中間色）に置き直すので、左右に継ぎ目が出ない。
// 単色にするのは、カードを横に並べたとき写真ごとの明暗（左が暗く右が明るい）が縞に見えないようにするため。
// 縦は元写真の上 0%〜86% を使う（それより下まで使うと、肩が元写真の端に触れたり、体が写真の下端で途切れたりする人がいるため）。
//
// 使い方（nowhere-group ディレクトリで）:
//   swift _build/tools/officer_wide.swift images/site/people/<名前>.jpg images/site/people/<名前>-wide.jpg
import CoreImage
import CoreImage.CIFilterBuiltins
import Vision

let a = CommandLine.arguments
let src = CIImage(contentsOf: URL(fileURLWithPath: a[1]))!
let (W, H) = (1330.0, 700.0)
let (top, bottom) = (0.0, 0.86)

let req = VNGeneratePersonSegmentationRequest(); req.qualityLevel = .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
try VNImageRequestHandler(ciImage: src).perform([req])
var mask = CIImage(cvPixelBuffer: req.results!.first!.pixelBuffer)
mask = mask.transformed(by: CGAffineTransform(scaleX: src.extent.width / mask.extent.width, y: src.extent.height / mask.extent.height))
// 背景側にわずかに残る値（元写真の背景がうっすら残り、四角い帯に見える）を消す：0.15 未満を 0 に、それ以上を引き伸ばす
let th = CIFilter.colorMatrix(); th.inputImage = mask
th.rVector = CIVector(x: 1.18, y: 0, z: 0, w: 0); th.biasVector = CIVector(x: -0.18, y: 0, z: 0, w: 0)
mask = th.outputImage!.applyingFilter("CIColorClamp")

// 元写真の上 top〜bottom が出力の高さいっぱいになるよう拡大し、左右中央に置く（CoreImage は左下原点）
let side = H / (bottom - top)
let place = CGAffineTransform(translationX: (W - side) / 2, y: H - side * (1 - top)).scaledBy(x: side / src.extent.width, y: side / src.extent.height)
let bg = CIImage(color: CIColor(red: 0xED / 255.0, green: 0xED / 255.0, blue: 0xE9 / 255.0))
let blend = CIFilter.blendWithMask()
blend.inputImage = src.transformed(by: place)
blend.maskImage = mask.transformed(by: place)
blend.backgroundImage = bg
let out = blend.outputImage!.cropped(to: CGRect(x: 0, y: 0, width: W, height: H))
try CIContext().writeJPEGRepresentation(of: out, to: URL(fileURLWithPath: a[2]), colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!,
                                        options: [kCGImageDestinationLossyCompressionQuality as CIImageRepresentationOption: 0.88])
