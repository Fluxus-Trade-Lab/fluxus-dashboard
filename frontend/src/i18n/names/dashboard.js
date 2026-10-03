// Data names first seen on the dashboard page (ETF, sector, industry, basket names).
// English name → Chinese. Merged into ZH_NAMES in ../names.js; a name defined
// twice fails names.test.js.
//
// These are the vendor names of the Industries and Sel Sectors ETFs
// (src/lib/etfNames.json) that the Leaders and Laggards cards print. Where a
// fund's name is a near-twin of a theme or industry already in names.js
// (Semiconductor / Semiconductors, Biotech / Biotechnology) it gets its own
// Chinese, because names.test.js forbids two English names sharing one.
export default {
  // sectors (Select Sector SPDRs)
  'Consumer Discretionary': '非必需消费',
  'Health Care': '医疗健康',
  'Industrial': '工业板块',
  'Materials': '原材料',

  // industry ETFs
  'Agriculture': '农业',
  'Artificial Intelligence & Technology': '人工智能与科技',
  'Autonomous & Electric Vehicles': '自动驾驶与电动车',
  'Bank': '银行',
  'Biotech': '生物技术',
  'Bitcoin': '比特币',
  'Bitcoin Mining': '比特币矿企',
  'Blockchain & Fintech Innovation': '区块链与金融科技创新',
  'Blockchain Technology': '区块链技术',
  'CSI China Internet': '中概互联网',
  'China': '中国',
  'China Large-Cap': '中国大盘股',
  'Cloud Computing': '云计算',
  'Commodity': '大宗商品',
  'Digital Payments': '数字支付',
  'Dow Jones Internet': '道琼斯互联网',
  'Dynamic Leisure and Entertainment': '休闲娱乐',
  'Expanded Tech-Software Sector': '科技软件',
  'Food & Beverage': '食品饮料',
  'Genomic Revolution': '基因革命',
  'Global Clean Energy': '全球清洁能源',
  'Global Shipping': '全球航运',
  'Health Care Equipment': '医疗设备',
  'Innovation': '颠覆式创新',
  'Jets': '航空业',
  'Junior Silver Miners': '小型银矿股',
  'Metals & Mining': '金属与采矿',
  'MicroSectors FANG+ ETN': 'FANG+ 科技巨头',
  'NASDAQ Cybersecurity': '纳斯达克网络安全',
  'NASDAQ-100 Equal Weighted': '纳指100等权',
  'Natural Gas': '天然气',
  'Oil': '原油',
  'Oil & Gas Exploration & Production': '油气勘探与生产',
  'Oil Services': '油田服务',
  'Online Retail': '网络零售',
  'Pharmaceutical': '制药',
  'Pure US Cannabis': '美国大麻',
  'Rare Earth and Strategic Metals': '稀土与战略金属',
  'Regional Banking': '地区银行业',
  'Residential and Multisector Real Estate': '住宅与多元地产',
  'Retail': '零售',
  'Robo Global Robotics and Automation': 'Robo Global 机器人',
  'Russell 2000': '罗素2000',
  'Semiconductor': '半导体板块',
  'Social Media': '社交媒体',
  'Transportation': '交通运输',
  'U.S. Aerospace & Defense': '美国航空航天与国防',
  'U.S. Infrastructure Development': '美国基建',
  'U.S. Medical Devices': '美国医疗器械',
  'U.S. REIT': '美国REIT',
  'U.S. Telecommunications': '美国电信',
}
