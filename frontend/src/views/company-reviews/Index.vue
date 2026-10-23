<template>
  <div class="business-page company-page">
    <main class="career-container">
      <BusinessPageHeader eyebrow="求职准备 / 企业与职位" title="找到值得进一步了解的机会" description="比较岗位要求、了解企业信息，把下一步准备落到具体的职位上。">
        <router-link to="/resume" class="career-button">完善简历</router-link>
        <router-link to="/company-reviews/senior-advice/form" class="career-button career-button-primary">分享经验</router-link>
      </BusinessPageHeader>
      <div class="business-tabs" role="tablist" aria-label="企业与职位内容">
        <button v-for="tab in companyTabs" :key="tab.id" type="button" role="tab" :aria-selected="activeTab === tab.id" @click="switchTab(tab.id)">{{ tab.label }}</button>
      </div>
      <div class="company-layout">
        <aside class="company-filters business-panel">
          <div class="business-panel-head"><h2>筛选职位</h2><button type="button" class="career-link" @click="resetJobFilters">重置</button></div>
          <div class="business-field"><label for="job-location">工作地点</label><select id="job-location" v-model="selectedJobLocation" @change="handleSearch"><option value="">全部地区</option><option v-for="location in jobLocationOptions" :key="location" :value="location">{{ location }}</option></select></div>
          <div class="business-field"><label for="job-industry">行业方向</label><select id="job-industry" v-model="selectedJobIndustry" @change="handleSearch"><option value="">全部行业</option><option v-for="industry in jobIndustryOptions" :key="industry" :value="industry">{{ industry }}</option></select></div>
          <div class="filter-note"><h3>先看要求，再做判断</h3><p>确认岗位职责、工作地点与申请渠道，结合自己的经历判断准备重点。</p><router-link to="/career-evaluation" class="career-link">查看我的职业规划 →</router-link></div>
        </aside>
        <section class="company-results" aria-label="职位与企业信息">
          <template v-if="activeTab === 'recommended'">
            <div class="job-search"><label class="sr-only" for="job-search">搜索职位</label><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5"/><path d="m13 13 4 4"/></svg><input id="job-search" v-model="searchKeyword" @input="handleSearch" type="search" placeholder="搜索职位、企业、地点或技能" /><button v-if="searchKeyword" type="button" class="career-link" @click="clearSearch">清空</button></div>
            <div class="job-results-summary"><span>找到 <strong>{{ filteredJobs.length }}</strong> 个职位</span><span>先了解岗位，再决定是否申请</span></div>
            <div v-if="jobsLoading" class="business-empty" role="status"><span class="loading loading-spinner loading-sm"></span><p>正在加载职位…</p></div>
            <div v-else-if="!filteredJobs.length" class="business-empty"><h2>暂时没有匹配的职位</h2><p>可以调整关键词和筛选条件，或稍后再来查看。</p><button type="button" class="career-button" @click="resetJobFilters">重置筛选</button></div>
            <div v-else class="job-results-list">
              <article v-for="job in currentFilteredJobs" :key="job.id" class="job-result-row">
                <div class="job-result-main"><h2>{{ job.title || '职位名称待补充' }}</h2><p class="job-company">{{ job.company }}</p><div class="job-tags"><span v-for="(tag,index) in job.tags" :key="index" class="business-tag">{{ tag }}</span></div><p class="job-description">{{ filterBrTags(job.jobDetails) || '暂无详细岗位说明，请查看招聘来源。' }}</p><p v-if="isCompanyDetailsValid(job.companyDetails)" class="job-company-detail">{{ filterBrTags(job.companyDetails) }}</p></div>
                <div class="job-result-side"><strong>{{ job.salary || '薪资待确认' }}</strong><a v-if="job.jobSourceUrl" :href="job.jobSourceUrl" target="_blank" rel="noopener noreferrer" class="career-button">查看职位 ↗</a><span v-else class="business-muted">暂无来源链接</span></div>
              </article>
              <div v-if="filteredJobsTotalPages > 1" class="business-pagination"><button type="button" class="career-button" :disabled="jobsPage === 1" @click="handleJobsPageChange(jobsPage - 1)">上一页</button><span>{{ jobsPage }} / {{ filteredJobsTotalPages }}</span><button type="button" class="career-button" :disabled="jobsPage >= filteredJobsTotalPages" @click="handleJobsPageChange(jobsPage + 1)">下一页</button></div>
            </div>
          </template>
          <section v-else-if="activeTab === 'red' || activeTab === 'black'" class="business-panel ranking-panel">
            <div class="business-panel-head"><h2>{{ activeTab === 'red' ? '企业推荐参考' : '求职风险参考' }}</h2><span class="business-tag">历史整理资料</span></div>
            <p class="business-muted">条目仅作了解企业与岗位的参考；招聘条件、薪资及评价需要结合原始信息核实。</p>
            <div class="ranking-table-wrap"><table class="ranking-table"><thead><tr><th>岗位 / 企业</th><th>地点</th><th>薪资</th><th>参考说明</th></tr></thead><tbody><tr v-for="item in rankingRows" :key="item.rank"><td><strong>{{ item.position }}</strong><span>{{ item.company }}</span></td><td>{{ item.location }}</td><td>{{ item.salary || '未提供' }}</td><td>{{ item.reason }}</td></tr></tbody></table></div>
            <div class="business-pagination"><button class="career-button" :disabled="rankingPage <= 1" @click="changeRankingPage(-1)">上一页</button><span>{{ rankingPage }} / {{ rankingPages }}</span><button class="career-button" :disabled="rankingPage >= rankingPages" @click="changeRankingPage(1)">下一页</button></div>
          </section>
          <section v-else-if="activeTab === 'safety'" class="business-panel safety-content"><h2>求职安全，先核对再行动</h2><p class="business-muted">遇到不确定的信息，先停下来核实，不用急着做决定。</p><article v-for="tip in safetyTips" :key="tip.title"><span class="safety-marker" aria-hidden="true"></span><div><h3>{{ tip.title }}</h3><p>{{ tip.text }}</p></div></article><div class="business-notice">保存招聘页面、沟通与付款记录；发生疑似诈骗时，通过平台官方渠道或当地公安机关求助。</div></section>
          <section v-else-if="activeTab === 'advice'" class="business-panel">
            <div class="business-panel-head"><h2>来自学长学姐的经验</h2><router-link to="/company-reviews/senior-advice/form" class="career-link">分享一条建议 →</router-link></div>
            <div class="advice-search"><input v-model="adviceSearchKeyword" type="search" aria-label="搜索建议中的企业或职位" placeholder="搜索企业或职位" /><select v-model="adviceFilter" aria-label="建议排序"><option value="">全部建议</option><option value="recent">最近发布</option><option value="high-rating">评分较高</option></select></div>
            <div v-if="adviceLoading" class="business-empty" role="status">正在加载建议…</div>
            <div v-else-if="!filteredAdviceList.length" class="business-empty"><h3>还没有匹配的经验分享</h3><p>可以换个关键词，或分享自己经历过的求职过程。</p></div>
            <article v-for="advice in filteredAdviceList" :key="advice.id" class="advice-row"><header><div><h3>{{ advice.company }}</h3><p>{{ advice.position }}</p></div><span class="business-tag">{{ advice.rating }} / 5</span></header><p class="advice-source">{{ advice.senior_name }} · {{ advice.graduation_year }} 届<span v-if="advice.current_company"> · {{ advice.current_company }}</span></p><p class="advice-body">{{ advice.advice }}</p><div class="advice-notes"><div v-if="advice.pros?.length"><strong>认可的方面</strong><p v-for="(item,index) in advice.pros" :key="index">{{ item }}</p></div><div v-if="advice.cons?.length"><strong>需要了解的方面</strong><p v-for="(item,index) in advice.cons" :key="index">{{ item }}</p></div></div></article>
            <div v-if="adviceTotalPages > 1" class="business-pagination"><button class="career-button" :disabled="advicePage <= 1" @click="handleAdvicePageChange(advicePage - 1)">上一页</button><span>{{ advicePage }} / {{ adviceTotalPages }}</span><button class="career-button" :disabled="advicePage >= adviceTotalPages" @click="handleAdvicePageChange(advicePage + 1)">下一页</button></div>
          </section>
        </section>
        <aside class="business-stack company-context">
          <section class="business-panel"><div class="business-panel-head"><h2>校园双选会</h2><span class="business-tag">招聘资讯</span></div><p v-if="loading" class="business-muted">正在加载…</p><p v-else-if="!jobFairs.length" class="business-muted">暂无双选会信息。</p><div v-for="fair in jobFairs" :key="fair.id" class="fair-row"><h3>{{ getUniversityName(fair.university) }}</h3><a :href="fair.university_url" target="_blank" rel="noopener noreferrer" class="career-link">{{ fair.name }} ↗</a></div><div v-if="totalCount > pageSize" class="business-pagination"><button class="career-button" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)">←</button><span>{{ currentPage }} / {{ Math.ceil(totalCount / pageSize) }}</span><button class="career-button" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(currentPage + 1)">→</button></div></section>
          <section class="business-panel"><h2>地区招聘资讯</h2><p v-if="!locationJobs.length" class="business-muted context-note">暂无地区资讯。可使用左侧工作地点筛选查看现有职位。</p><div v-for="job in locationJobs.slice(0,3)" :key="job.id" class="fair-row"><h3>{{ job.position_name }}</h3><p class="business-muted">{{ job.company_name }} · {{ job.address }}</p><span v-if="job.salary_range" class="business-tag">{{ job.salary_range }}</span></div></section>
          <section class="company-preparation"><p class="career-eyebrow">下一步准备</p><h2>对照岗位，整理自己的经历</h2><p>先写清负责的任务、做过的选择与验证结果，再练习如何把它们讲出来。</p><router-link to="/interview" class="career-link">练习一次模拟面试 →</router-link></section>
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import BusinessPageHeader from '@/components/BusinessPageHeader.vue'
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { jobFairAPI, computerCareerAPI, apiFetch } from '@/api'
import { IP_GEOLOCATION_URL } from '@/config'
import api from '@/api'

const router = useRouter()

// 搜索查询
const searchQuery = ref('')

// 双选会数据
const jobFairs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(8)
const totalCount = ref(0)

// 高校名称映射
const universityNameMap = {
  'csu': '中南大学',
  'hnu': '湖南大学',
  'hunnu_science': '湖南师范大学',
  'csust': '长沙理工大学',
  'hunnu': '湖南农业大学',
  'csuft': '中南林业科技大学',
  'hnu_medicine': '湖南医药学院',
  'xtu': '湘潭大学',
  'hnust': '湖南科技大学',
  'usc': '南华大学',
  'hutb': '湖南工商大学',
  'hnctu': '湖南工业大学',
  'jsu': '吉首大学',
  'hhtc': '怀化学院',
  'hnfnu': '湖南第一师范学院',
  'hufe': '湖南财政经济学院',
  'hnxxy': '湖南信息学院',
  'hnyxy': '湖南应用技术学院',
  'hnist': '湖南理工学院',
  'hynu': '衡阳师范学院',
  'huas': '湖南文理学院',
  'hnjcxy': '湖南警察学院',
  'hngxy': '湖南工学院',
  'syxy': '邵阳学院',
  'xnu': '湘南学院',
  'hnrwkjxy': '湖南人文科技学院',
  'hnjtgcxy': '湖南交通工程学院',
  'hnrjzy': '湖南软件职业技术大学',
  'other': '其他高校'
}

// 获取高校名称
const getUniversityName = (universityCode) => {
  return universityNameMap[universityCode] || universityCode
}

// 地区招聘资讯
const locationStatus = ref('loading')
const currentCity = ref('')
const locationJobs = ref([])

const getCityFromIP = async () => {
  if (!IP_GEOLOCATION_URL) return null
  try {
    console.log('[Geolocation Debug] 使用 IP 地址获取城市（仅精确到市）')
    const response = await fetch(IP_GEOLOCATION_URL)
    const data = await response.json()
    console.log('[Geolocation Debug] IP 地理定位响应:', data)

    if (data.status === 'success') {
      // 只使用 city 字段，确保只精确到市级别
      if (data.city && data.city.trim()) {
        console.log(`[Geolocation Debug] IP定位城市: ${data.city}`)
        return data.city
      }
      // 如果没有 city，使用 regionName（省级）作为备选
      if (data.regionName && data.regionName.trim()) {
        console.log(`[Geolocation Debug] IP定位地区: ${data.regionName}`)
        return data.regionName
      }
    }
    console.log('[Geolocation Debug] IP定位失败，使用默认城市: 北京')
    return '北京'
  } catch (error) {
    console.error('[Geolocation Debug] IP 地理定位失败:', error)
    return '北京'
  }
}

const getLocationAndLoadJobs = async () => {
  console.log('[Geolocation Debug] 开始获取位置信息（使用免费 IP 定位）')

  try {
    // 直接使用 IP 定位（免费服务）
    const city = await getCityFromIP()
    currentCity.value = city
    console.log(`[Geolocation Debug] IP定位获取城市: ${city}`)
    await loadJobsByCity(city)

  } catch (error) {
    console.error('[Geolocation Debug] IP定位失败:', error)
    // 使用默认城市
    currentCity.value = '长沙'
    await loadJobsByCity('长沙')
  }
}

// 地区层级映射表（区 -> 市 -> 省）
const regionHierarchy = {
  // 长沙地区
  '天心区': { city: '长沙市', province: '湖南省' },
  '岳麓区': { city: '长沙市', province: '湖南省' },
  '芙蓉区': { city: '长沙市', province: '湖南省' },
  '开福区': { city: '长沙市', province: '湖南省' },
  '雨花区': { city: '长沙市', province: '湖南省' },
  '望城区': { city: '长沙市', province: '湖南省' },
  '长沙县': { city: '长沙市', province: '湖南省' },
  '宁乡市': { city: '长沙市', province: '湖南省' },
  '浏阳市': { city: '长沙市', province: '湖南省' },

  // 益阳地区
  '赫山区': { city: '益阳市', province: '湖南省' },
  '赫山': { city: '益阳市', province: '湖南省' },
  '资阳区': { city: '益阳市', province: '湖南省' },
  '沅江市': { city: '益阳市', province: '湖南省' },

  // 北京
  '北京': { city: '北京市', province: '北京市' },
  '东城区': { city: '北京市', province: '北京市' },
  '西城区': { city: '北京市', province: '北京市' },
  '朝阳区': { city: '北京市', province: '北京市' },
  '海淀区': { city: '北京市', province: '北京市' },

  // 上海
  '上海': { city: '上海市', province: '上海市' },
  '黄浦区': { city: '上海市', province: '上海市' },
  '徐汇区': { city: '上海市', province: '上海市' },
  '浦东新区': { city: '上海市', province: '上海市' },

  // 广州
  '广州': { city: '广州市', province: '广东省' },
  '天河区': { city: '广州市', province: '广东省' },
  '越秀区': { city: '广州市', province: '广东省' },
  '海珠区': { city: '广州市', province: '广东省' },

  // 深圳
  '深圳': { city: '深圳市', province: '广东省' },
  '南山区': { city: '深圳市', province: '广东省' },
  '福田区': { city: '深圳市', province: '广东省' },
  '宝安区': { city: '深圳市', province: '广东省' },

  // 杭州
  '杭州': { city: '杭州市', province: '浙江省' },
  '西湖区': { city: '杭州市', province: '浙江省' },
  '滨江区': { city: '杭州市', province: '浙江省' },

  // 成都
  '成都': { city: '成都市', province: '四川省' },
  '锦江区': { city: '成都市', province: '四川省' },
  '高新区': { city: '成都市', province: '四川省' },

  // 武汉
  '武汉': { city: '武汉市', province: '湖北省' },
  '武昌区': { city: '武汉市', province: '湖北省' },
  '洪山区': { city: '武汉市', province: '湖北省' },

  // 湖南省其他城市
  '益阳市': { city: '益阳市', province: '湖南省' },
  '岳阳市': { city: '岳阳市', province: '湖南省' },
  '株洲市': { city: '株洲市', province: '湖南省' },
  '湘潭市': { city: '湘潭市', province: '湖南省' },
  '衡阳市': { city: '衡阳市', province: '湖南省' },
  '常德市': { city: '常德市', province: '湖南省' },
  '郴州市': { city: '郴州市', province: '湖南省' },
  '永州市': { city: '永州市', province: '湖南省' },
  '邵阳市': { city: '邵阳市', province: '湖南省' },
  '娄底市': { city: '娄底市', province: '湖南省' },
  '怀化市': { city: '怀化市', province: '湖南省' },
  '张家界市': { city: '张家界市', province: '湖南省' },

  // 城市直接映射
  '长沙市': { city: '长沙市', province: '湖南省' },
  '北京市': { city: '北京市', province: '北京市' },
  '上海市': { city: '上海市', province: '上海市' },
  '广州市': { city: '广州市', province: '广东省' },
  '深圳市': { city: '深圳市', province: '广东省' },
  '杭州市': { city: '杭州市', province: '浙江省' },
  '成都市': { city: '成都市', province: '四川省' },
  '武汉市': { city: '武汉市', province: '湖北省' },

  // 省级直接映射
  '湖南省': { city: '湖南省', province: '湖南省' },
  '广东省': { city: '广东省', province: '广东省' },
  '浙江省': { city: '浙江省', province: '浙江省' },
  '四川省': { city: '四川省', province: '四川省' },
  '湖北省': { city: '湖北省', province: '湖北省' },
  '北京市': { city: '北京市', province: '北京市' },
  '上海市': { city: '上海市', province: '上海市' },
  '湖南': { city: '湖南省', province: '湖南省' },
  '广东': { city: '广东省', province: '广东省' },
  '浙江': { city: '浙江省', province: '浙江省' },
  '四川': { city: '四川省', province: '四川省' },
  '湖北': { city: '湖北省', province: '湖北省' }
}

// 获取地区层级信息
const getRegionHierarchy = (location) => {
  if (!location) return { district: null, city: null, province: null }

  // 如果在映射表中找到
  if (regionHierarchy[location]) {
    return {
      district: location,
      ...regionHierarchy[location]
    }
  }

  // 尝试去除后缀后查找
  const suffixes = ['区', '县', '市', '市辖区', '自治县', '旗']
  for (const suffix of suffixes) {
    if (location.endsWith(suffix)) {
      const baseName = location.slice(0, -suffix.length)
      if (regionHierarchy[baseName]) {
        return {
          district: location,
          ...regionHierarchy[baseName]
        }
      }
    }
  }

  // 默认返回
  return {
    district: location,
    city: location,
    province: location
  }
}

// 逐级查询职位：区 -> 市 -> 省
const loadJobsByCity = async (location) => {
  try {
    console.log(`[Geolocation Debug] 开始逐级查询职位，起点: ${location}`)

    // 获取地区层级
    const hierarchy = getRegionHierarchy(location)
    console.log(`[Geolocation Debug] 地区层级:`, hierarchy)

    // 查询顺序：区 → 市 → 省
    const searchLevels = []

    if (hierarchy.district && hierarchy.district !== hierarchy.city) {
      searchLevels.push({ level: 'district', value: hierarchy.district, label: `${hierarchy.district}(区/县)` })
    }
    if (hierarchy.city) {
      searchLevels.push({ level: 'city', value: hierarchy.city, label: `${hierarchy.city}(市)` })
    }
    if (hierarchy.province && hierarchy.province !== hierarchy.city) {
      searchLevels.push({ level: 'province', value: hierarchy.province, label: `${hierarchy.province}(省)` })
    }

    console.log(`[Geolocation Debug] 查询层级顺序:`, searchLevels.map(s => s.label))

    // 逐级查询
    for (const level of searchLevels) {
      console.log(`[Geolocation Debug] 正在查询 ${level.label}: ${level.value}`)

      // 使用后端API的address参数进行查询
      const searchUrl = `/career-evaluation/computer-careers/?address=${encodeURIComponent(level.value)}`
      console.log(`[Geolocation Debug] API地址: ${searchUrl}`)

      try {
        const searchResponse = await apiFetch(searchUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        console.log(`[Geolocation Debug] HTTP状态码: ${searchResponse.status}`)

        if (!searchResponse.ok) {
          console.error(`[Geolocation Debug] HTTP错误: ${searchResponse.status} - ${searchResponse.statusText}`)
          continue
        }

        const searchData = await searchResponse.json()
        console.log(`[Geolocation Debug] ${level.label}查询结果:`, searchData)

        if (searchData.results && searchData.results.length > 0) {
          locationJobs.value = searchData.results
          currentCity.value = level.value
          console.log(`[Geolocation Debug] ✅ 在 ${level.label} 级别找到 ${locationJobs.value.length} 个职位`)
          locationStatus.value = 'success'
          return
        }

      } catch (fetchError) {
        console.error(`[Geolocation Debug] ${level.label}查询失败:`, fetchError)
      }

      console.log(`[Geolocation Debug] ❌ ${level.label} 级别没有找到职位，继续上一级`)
    }

    // 如果所有级别都没有结果，尝试直接查询所有数据并在前端筛选
    console.log('[Geolocation Debug] 尝试获取所有职位数据进行前端筛选')
    try {
      const allJobsResponse = await computerCareerAPI.getComputerCareers(1, 100)
      console.log('[Geolocation Debug] 获取所有职位总数:', allJobsResponse.results?.length || 0)

      if (allJobsResponse.results && allJobsResponse.results.length > 0) {
        // 在前端进行模糊匹配
        for (const level of searchLevels) {
          const matched = allJobsResponse.results.filter(job =>
            job.address && (job.address.includes(level.value) || level.value.includes(job.address))
          )
          console.log(`[Geolocation Debug] 前端筛选 ${level.label} (${level.value}): ${matched.length} 条`)

          if (matched.length > 0) {
            locationJobs.value = matched
            currentCity.value = level.value
            console.log(`[Geolocation Debug] ✅ 前端筛选在 ${level.label} 级别找到 ${matched.length} 个职位`)
            locationStatus.value = 'success'
            return
          }
        }
      }
    } catch (error) {
      console.error('[Geolocation Debug] 获取所有职位失败:', error)
    }

    // 如果所有级别都没有结果
    console.log('[Geolocation Debug] ❌ 所有级别都没有找到职位')
    locationJobs.value = []
    currentCity.value = location
    locationStatus.value = 'success'

  } catch (error) {
    console.error('[Geolocation Debug] 职位查询失败:', error)
    locationJobs.value = []
    locationStatus.value = 'success'
  }
}

// 职位数据
const jobs = ref([])
const jobsLoading = ref(false)
const jobsPage = ref(1)
const jobsPageSize = ref(10)
const jobsTotalCount = ref(0)

// 搜索相关
const searchKeyword = ref('')

// 过滤后的职位数据
const selectedJobLocation = ref('')
const selectedJobIndustry = ref('')
const jobLocationOptions = computed(() => [...new Set(jobs.value.map(job => job.tags?.[0]).filter(Boolean))].sort())
const jobIndustryOptions = computed(() => [...new Set(jobs.value.map(job => job.tags?.[1]).filter(Boolean))].sort())
const filteredJobs = computed(() => {
  const keyword = searchKeyword.value.toLowerCase().trim()
  return jobs.value.filter(job => {
    if (selectedJobLocation.value && job.tags?.[0] !== selectedJobLocation.value) return false
    if (selectedJobIndustry.value && job.tags?.[1] !== selectedJobIndustry.value) return false
    return !keyword || [job.title, job.company, ...(job.tags || []), job.jobDetails, job.companyDetails]
      .some(value => String(value || '').toLowerCase().includes(keyword))
  })
})
function resetJobFilters() {
  selectedJobLocation.value = ''
  selectedJobIndustry.value = ''
  clearSearch()
}

// 搜索处理
const handleSearch = async () => {
  console.log('搜索关键词:', searchKeyword.value)
  // 搜索时重置到第一页
  jobsPage.value = 1
}

// 清空搜索
const clearSearch = async () => {
  searchKeyword.value = ''
  console.log('搜索已清空')
  // 清空搜索后重置到第一页
  jobsPage.value = 1
}

// 标签页状态
const activeTab = ref('recommended')

// 红榜数据
const redListData = ref([
  { rank: 1, position: 'C/C++', company: '外企德科数字技术有限公司', location: '上海-青浦区', salary: '1.7-3万·16薪', reason: '高薪、知名大厂（华为系）、技术核心' },
  { rank: 2, position: 'Java', company: '外企德科数字技术有限公司', location: '深圳-龙岗区', salary: '1.5-3万·14薪', reason: '高薪、知名大厂、16薪、技术核心' },
  { rank: 3, position: '科研人员', company: '中国信息通信研究院', location: '北京-海淀区', salary: '1.9-2.1万', reason: '国家级科研机构、薪资高、稳定' },
  { rank: 4, position: '科研人员', company: '中国科学院微电子研究所', location: '北京-朝阳区', salary: '2-3万', reason: '中科院平台、薪资高、学术背景强' },
  { rank: 5, position: '科研人员', company: '浙江大学绍兴研究院', location: '绍兴-越城区', salary: '1.6-3万·15薪', reason: '高校平台、薪资优厚、福利好（15薪）' },
  { rank: 6, position: 'Java', company: '外企德科数字技术有限公司', location: '西安-雁塔区', salary: '1.6-3万·14薪', reason: '高薪、知名大厂、14薪' },
  { rank: 7, position: '测试工程师', company: '深圳市新凯来技术有限公司', location: '深圳-龙岗区', salary: '2-4万·15薪', reason: '高薪（2-4万）、行业领先、福利优厚' },
  { rank: 8, position: '科研人员', company: '中国科学院上海应用物理研究所', location: '上海-嘉定区', salary: '1.2-2万', reason: '中科院平台、科研导向、稳定' },
  { rank: 9, position: '技术支持工程师', company: '北京飞斯科科技有限公司', location: '北京-海淀区', salary: '1-1.5万', reason: '硕士起、专业对口、技术性强' },
  { rank: 10, position: 'C/C++', company: '联合汽车电子有限公司（UAES）', location: '重庆-渝北区', salary: '1.2-1.5万·17薪', reason: '知名合资企业、17薪、技术核心' },
  { rank: 11, position: '测试工程师', company: '中电科思仪科技股份有限公司', location: '青岛-None', salary: '6000-8000元', reason: '央企背景、稳定、福利好' },
  { rank: 12, position: '科研人员', company: '龙子湖新能源实验室', location: '郑州-金水区', salary: '1.4-2万', reason: '省实验室平台、薪资高、博士优先' },
  { rank: 13, position: 'Java', company: '外企德科数字技术有限公司', location: '南京-雨花台区', salary: '1.8-3.5万·16薪', reason: '高薪、大厂背景、16薪' },
  { rank: 14, position: '技术支持工程师', company: '上海柏楚电子科技股份有限公司', location: '上海-闵行区', salary: '8000-12000元·15薪', reason: '科创板上市企业、15薪、福利好' },
  { rank: 15, position: '科研人员', company: '中国信息通信研究院', location: '北京-海淀区', salary: '1.9-2.1万', reason: '国家级科研机构、薪资高、稳定' },
  { rank: 16, position: 'C/C++', company: '北京瑞鑫天算资产管理有限公司', location: '北京-海淀区', salary: '1.5-3万', reason: '量化私募、薪资高、对技术有热情' },
  { rank: 17, position: '科研人员', company: '河南省科学院高能物理研究中心', location: '郑州-金水区', salary: '1.5-3万', reason: '省级科研平台、薪资高、博士进编' },
  { rank: 18, position: '科研人员', company: '清华大学合肥公共安全研究院', location: '合肥-蜀山区', salary: '1.2-2.4万·15薪', reason: '顶尖高校研究院、15薪、科研导向' },
  { rank: 19, position: '实施工程师', company: '南京高速齿轮制造有限公司', location: '南京-江宁区', salary: '1-1.2万·15薪', reason: '上市公司、15薪、发展前景好' },
  { rank: 20, position: 'C/C++', company: '外企德科数字技术有限公司', location: '苏州-工业园区', salary: '1.5-3万·15薪', reason: '高薪、大厂背景、15薪' },
  { rank: 21, position: '科研人员', company: '北京大学深圳研究院', location: '深圳-南山区', salary: '8000-10000元', reason: '顶尖高校平台、学术环境好' },
  { rank: 22, position: '技术支持工程师', company: '江苏富科思科技有限公司', location: '南京-鼓楼区', salary: '7000-10000元', reason: '中科院院士团队、技术前沿' },
  { rank: 23, position: 'Java', company: '外企德科数字技术有限公司', location: '杭州-滨江区', salary: '1.5-3万·14薪', reason: '高薪、大厂背景、14薪' },
  { rank: 24, position: '实施工程师', company: '浪潮集团', location: '杭州-西湖区', salary: '1.2-2.2万', reason: '知名IT企业、薪资高、发展稳定' },
  { rank: 25, position: '科研人员', company: '浙江清华长三角研究院', location: '嘉兴-南湖区', salary: '1.5-2万', reason: '清华研究院平台、薪资高' },
  { rank: 26, position: 'C/C++', company: '外企德科数字技术有限公司', location: '成都-郫都区', salary: '1.5-3万', reason: '高薪、大厂背景' },
  { rank: 27, position: '科研人员', company: '中国科学院长春应用化学研究所', location: '长春-朝阳区', salary: '1-2万', reason: '中科院平台、稳定、博士优先' },
  { rank: 28, position: '软件测试', company: '博彦科技承德有限公司', location: '西安-雁塔区', salary: '120-130元/天', reason: '知名IT公司、实习机会、26届可投' },
  { rank: 29, position: '技术支持工程师', company: '深圳市北电仪表有限公司', location: '深圳-南山区', salary: '5000-10000元', reason: '双休、有住宿、发展空间大' },
  { rank: 30, position: '前端开发', company: '四川锐狐网络科技有限公司', location: '成都-锦江区', salary: '3000-5000元', reason: '双休、明确培养26/27届、有转正机会' },
  { rank: 31, position: '科研人员', company: '中国船舶集团有限公司第七六〇研究所', location: '大连-中山区', salary: '8000-12000元', reason: '船舶军工研究所、稳定、技术强' },
  { rank: 32, position: 'C/C++', company: '外企德科数字技术有限公司', location: '武汉-江夏区', salary: '1.1-2.2万', reason: '高薪、大厂背景' },
  { rank: 33, position: '测试工程师', company: '中国汽车技术研究中心有限公司', location: '广州-增城区', salary: '面议', reason: '央企、行业龙头、发展前景好' },
  { rank: 34, position: '实施工程师', company: '北京冠群信息技术股份有限公司', location: '南京-浦口区', salary: '1.1-1.6万', reason: '知名企业、海外机会、双休' },
  { rank: 35, position: '技术支持工程师', company: '超年实业(上海)有限公司', location: '上海-松江区', salary: '6000-8000元', reason: '五险一金、双休、技术培训' },
  { rank: 36, position: '科研人员', company: '国防科技大学电子科学学院', location: '长沙-开福区', salary: '1-2万', reason: '军校平台、稳定、薪资待遇好' },
  { rank: 37, position: '测试工程师', company: '中船海丰航空科技有限公司', location: '北京-丰台区', salary: '1-1.6万·13薪', reason: '中船集团背景、13薪、福利好' },
  { rank: 38, position: '科研人员', company: '上海建科咨询集团股份有限公司', location: '上海-闵行区', salary: '2-3万', reason: '国企背景、薪资高、科研平台' },
  { rank: 39, position: '实施工程师', company: '上海柏楚电子科技股份有限公司', location: '济南-历下区', salary: '8000-12000元·15薪', reason: '科创板上市公司、15薪' },
  { rank: 40, position: 'Java', company: '外企德科数字技术有限公司', location: '杭州-滨江区', salary: '1.5-3万·15薪', reason: '高薪、15薪、核心业务' },
  { rank: 41, position: '科研人员', company: '国汽轻量化(江苏)汽车技术有限公司', location: '扬州-邗江区', salary: '6000-12000元', reason: '新型研发机构、硕士起、技术前沿' },
  { rank: 42, position: '技术支持工程师', company: '深圳市合杰电子有限公司', location: '苏州-吴中区', salary: '6000-7000元', reason: '大小周但提供专业培训、发展空间大' },
  { rank: 43, position: '测试工程师', company: '上海微创软件股份有限公司', location: '深圳-南山区', salary: '8000-13000元', reason: '知名外企、五险一金、双休' },
  { rank: 44, position: '实施工程师', company: '浪潮集团', location: '西安-未央区', salary: '1-1.5万·13薪', reason: '浪潮集团、13薪、智慧矿山方向' },
  { rank: 45, position: '技术支持工程师', company: '北京飞斯科科技有限公司', location: '北京-海淀区', salary: '1-1.5万', reason: '硕士起、专业对口、技术性强' },
  { rank: 46, position: '科研人员', company: '浙江大学绍兴研究院', location: '绍兴-越城区', salary: '1.6-3万·15薪', reason: '高校平台、薪资优厚、福利好' },
  { rank: 47, position: '前端开发', company: '湖南恒昌医药集团股份有限公司', location: '长沙-开福区', salary: '1.5-2.3万·13薪', reason: '医药集团、薪资高、13薪' },
  { rank: 48, position: '测试工程师', company: '广州赛西标准检测研究院有限公司', location: '广州-黄埔区', salary: '1-2万', reason: '五险一金、双休、技术驱动' },
  { rank: 49, position: '技术支持工程师', company: '浙江浙仪控股集团有限公司', location: '杭州-钱塘区', salary: '2.5-3万', reason: '博士后岗位、薪资极高、科研前沿' },
  { rank: 50, position: 'Java', company: '外企德科数字技术有限公司', location: '广州-白云区', salary: '1.4-2.8万·14薪', reason: '高薪、大厂背景、14薪' }
])

// 红榜分页
const redListPage = ref(1)
const redListPageSize = ref(10)

// 黑榜数据
const blackListData = ref([
  { rank: 1, position: '软件测试', company: '麦田房产', location: '北京-海淀区', salary: '1.5-1.7万', reason: 'JD与岗位不符：实为房产销售，职位描述与“软件测试”完全无关，误导求职者。' },
  { rank: 2, position: '测试工程师', company: '河南歌络影视传媒有限公司', location: '开封-龙亭区', salary: '9000-15000元', reason: '公司背景不符：影视传媒公司招聘测试工程师，岗位描述模糊，无具体技术栈。' },
  { rank: 3, position: '测试工程师', company: '河南歌络影视传媒有限公司', location: '开封-龙亭区', salary: '8000-9000元·13薪', reason: '公司背景不符：同上，一家影视传媒公司发布大量测试、车载测试岗，存在较大风险。' },
  { rank: 4, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '成都-成华区', salary: '6000-10000元', reason: '外包性质：人力资源公司发布，岗位JD模板化，薪资虚高，实际可能是外派岗位。' },
  { rank: 5, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '成都-武侯区', salary: '8000-11000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化，薪资吸引力高但需警惕。' },
  { rank: 6, position: '测试工程师', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 7, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '南昌-新建区', salary: '6000-9000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 8, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 9, position: '测试工程师', company: '青岛瑞晟元人力资源有限公司', location: '长春-朝阳区', salary: '1-1.2万·13薪', reason: '外包性质：人力资源公司发布，JD模板化，无具体业务描述。' },
  { rank: 10, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '焦作-山阳区', salary: '6000-9000元', reason: '外包性质：人力资源公司发布，岗位描述与“硬件测试”无关，内容混乱。' },
  { rank: 11, position: '软件测试', company: '青岛瑞晟元人力资源有限公司', location: '北京-海淀区', salary: '1.5-2万·13薪', reason: '外包性质：人力资源公司发布，JD模板化，内容为空。' },
  { rank: 12, position: '软件测试', company: '青岛瑞晟元人力资源有限公司', location: '镇江-润州区', salary: '1.5-2万·13薪', reason: '外包性质：同上，人力资源公司发布，JD模板化，内容为空。' },
  { rank: 13, position: '测试工程师', company: '青岛瑞晟元人力资源有限公司', location: '郑州-金水区', salary: '1-1.2万·13薪', reason: '外包性质：同上，人力资源公司发布，JD模板化。' },
  { rank: 14, position: '软件测试', company: '青岛瑞晟元人力资源有限公司', location: '长沙-岳麓区', salary: '8000-10000元', reason: '外包性质：同上，人力资源公司发布，JD模板化。' },
  { rank: 15, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '7000-12000元', reason: '外包性质：人力资源公司发布，薪资虚高，岗位描述混乱。' },
  { rank: 16, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 17, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-二七区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 18, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '焦作-修武县', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 19, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '焦作-解放区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 20, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '重庆-丰都县', salary: '8000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 21, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '东莞-None', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 22, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '南昌-新建区', salary: '6000-9000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 23, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 24, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '成都-锦江区', salary: '7000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 25, position: '测试工程师', company: '重庆科满福人力资源服务有限公司', location: '抚州-南城县', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 26, position: '测试工程师', company: '重庆科满福人力资源服务有限公司', location: '抚州-南丰县', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
])

// 学长学姐建议数据
const adviceList = ref([])
const adviceLoading = ref(false)
const advicePage = ref(1)
const advicePageSize = ref(10)
const adviceTotalPages = ref(1)
const adviceSearchKeyword = ref('')
const adviceFilter = ref('')

// 过滤后的建议
const filteredAdviceList = computed(() => {
  let filtered = adviceList.value
  if (adviceSearchKeyword.value) {
    const keyword = adviceSearchKeyword.value.toLowerCase()
    filtered = filtered.filter(advice =>
      advice.company.toLowerCase().includes(keyword) ||
      advice.position.toLowerCase().includes(keyword)
    )
  }

  if (adviceFilter.value === 'high-rating') {
    filtered.sort((a, b) => b.rating - a.rating)
  } else if (adviceFilter.value === 'recent') {
    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }

  return filtered
})

// 加载建议数据
const loadAdviceData = async () => {
  adviceLoading.value = true
  try {
    const response = await api.get('/ai/senior-advice/')
    adviceList.value = response.results || []
    adviceTotalPages.value = Math.ceil((response.count || 0) / advicePageSize.value)
  } catch (error) {
    console.error('加载建议数据失败:', error)
  } finally {
    adviceLoading.value = false
  }
}

// 建议分页
const handleAdvicePageChange = (page) => {
  if (page >= 1 && page <= adviceTotalPages.value) {
    advicePage.value = page
    loadAdviceData()
  }
}

// 黑榜分页
const blackListPage = ref(1)
const blackListPageSize = ref(10)

// 获取双选会数据
const fetchJobFairs = async () => {
  try {
    loading.value = true
    const response = await jobFairAPI.getJobFairs(currentPage.value, pageSize.value)
    jobFairs.value = response.results
    totalCount.value = response.count
  } catch (error) {
    console.error('获取双选会数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取职位数据
const fetchJobs = async () => {
  try {
    jobsLoading.value = true
    // 尝试调用计算机职业API
    try {
      // 先获取第一页数据，了解总数量
      const firstPageResponse = await computerCareerAPI.getComputerCareers(1, 100)
      let allJobs = firstPageResponse.results
      const totalCount = firstPageResponse.count

      // 计算需要获取的页数
      const totalPages = Math.ceil(totalCount / 100)

      // 如果有更多页，继续获取
      if (totalPages > 1) {
        const fetchPromises = []
        for (let page = 2; page <= totalPages; page++) {
          fetchPromises.push(computerCareerAPI.getComputerCareers(page, 100))
        }

        // 并行获取所有页数据
        const responses = await Promise.all(fetchPromises)
        responses.forEach(response => {
          allJobs = [...allJobs, ...response.results]
        })
      }

      // 转换数据结构
      jobs.value = allJobs.map(item => ({
        id: item.id,
        title: item.position_name,
        company: item.company_name,
        salary: item.salary_range,
        tags: [item.address, item.industry].filter(Boolean),
        jobDetails: item.position_details,
        companyDetails: item.company_details,
        jobSourceUrl: item.position_source_url
      }))
      jobsTotalCount.value = totalCount
      console.log('成功获取所有计算机职业数据，共', jobs.value.length, '条')
    } catch (apiError) {
      console.error('调用API失败')
    }
  } catch (error) {
    console.error('获取职位数据失败:', error)
  } finally {
    jobsLoading.value = false
  }
}

// 分页处理
const handlePageChange = (page) => {
  currentPage.value = page
  fetchJobFairs()
}

// 职位分页处理
const handleJobsPageChange = (page) => {
  jobsPage.value = page
  fetchJobs()
}

// 计算职位总页数
const jobsTotalPages = computed(() => {
  return Math.ceil(jobsTotalCount.value / jobsPageSize.value)
})

// 计算过滤后职位总页数
const filteredJobsTotalPages = computed(() => {
  return Math.ceil(filteredJobs.value.length / jobsPageSize.value)
})

// 计算当前页显示的过滤后职位
const currentFilteredJobs = computed(() => {
  const start = (jobsPage.value - 1) * jobsPageSize.value
  const end = start + jobsPageSize.value
  return filteredJobs.value.slice(start, end)
})

// 生命周期
onMounted(async () => {
  try {
    // 并行加载数据，避免阻塞
    await Promise.all([
      fetchJobFairs(),
      fetchJobs(),
      loadAdviceData(),
      getLocationAndLoadJobs()
    ])

    console.log('所有数据加载完成')
  } catch (error) {
    console.error('数据加载失败:', error)
  }
})

// 标签页切换
const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'red') {
    redListPage.value = 1
  }
}

// 红榜分页处理
const handleRedListPageChange = (page) => {
  redListPage.value = page
}

// 计算当前红榜页数据
const currentRedListData = computed(() => {
  const start = (redListPage.value - 1) * redListPageSize.value
  const end = start + redListPageSize.value
  return redListData.value.slice(start, end)
})

// 计算红榜总页数
const redListTotalPages = computed(() => {
  return Math.ceil(redListData.value.length / redListPageSize.value)
})

// 计算当前黑榜页数据
const currentBlackListData = computed(() => {
  const start = (blackListPage.value - 1) * blackListPageSize.value
  const end = start + blackListPageSize.value
  return blackListData.value.slice(start, end)
})

// 计算黑榜总页数
const blackListTotalPages = computed(() => {
  return Math.ceil(blackListData.value.length / blackListPageSize.value)
})



// 模拟地区招聘资讯
const regionNews = ref([
  {
    id: 1,
    type: '双选会',
    date: '3月25日',
    title: '2024春季计算机专场双选会',
    location: '清华大学 - 综合体育馆',
    locationIcon: 'apartment'
  },
  {
    id: 2,
    type: '宣讲会',
    date: '3月22日 19:00',
    title: '米哈游 2024 春招宣讲会',
    location: '上海交通大学 - 闵行校区',
    locationIcon: 'school'
  },
  {
    id: 3,
    type: '职场沙龙',
    date: '3月28日',
    title: '大厂面试官一对一辅导',
    location: '线上直播间 / 腾讯会议',
    locationIcon: 'video_chat'
  }
])

// 模拟热度飙升企业
const trendingCompanies = ref([
  {
    id: 1,
    rank: '01',
    name: '字节跳动 (ByteDance)',
    description: '今日搜索量 +240%'
  },
  {
    id: 2,
    rank: '02',
    name: '米哈游 (miHoYo)',
    description: '福利评价热度极高'
  }
])

// 导航到简历管理页面
const navigateToResume = () => {
  router.push('/resume')
}

// 导航到面试页面
const navigateToInterview = () => {
  router.push('/interview')
}

// 过滤 br 标签的函数
const filterBrTags = (text) => {
  if (!text) return ''
  return text.replace(/<br\s*\/?>/g, ' ')
}

// 过滤 nan 数据的函数
const isCompanyDetailsValid = (companyDetails) => {
  if (!companyDetails) return false
  const cleaned = companyDetails.trim().toLowerCase()
  return cleaned !== 'nan' && cleaned !== 'null' && cleaned !== 'undefined'
}

const companyTabs = [
  { id: 'recommended', label: '推荐职位' }, { id: 'red', label: '企业推荐参考' },
  { id: 'black', label: '风险参考' }, { id: 'safety', label: '求职安全' }, { id: 'advice', label: '学长学姐建议' },
]
const safetyTips = [
  { title: '先核实企业与招聘渠道', text: '通过企业官网和正式招聘页面核对岗位，注意沟通账号与招聘主体是否一致。' },
  { title: '谨慎对待付费与贷款要求', text: '遇到押金、培训贷款、付费内推等要求，先暂停操作并通过官方渠道核实。' },
  { title: '保护个人信息和账户', text: '不向陌生人提供验证码、支付密码或远程控制权限，谨慎提交超出招聘所需的资料。' },
  { title: '仔细确认书面约定', text: '核对工作地点、岗位职责、薪资结构、试用期及合同主体，保留沟通记录。' },
]
const rankingRows = computed(() => activeTab.value === 'red' ? currentRedListData.value : currentBlackListData.value)
const rankingPage = computed(() => activeTab.value === 'red' ? redListPage.value : blackListPage.value)
const rankingPages = computed(() => activeTab.value === 'red' ? redListTotalPages.value : Math.max(1, Math.ceil(blackListData.value.length / blackListPageSize.value)))
function changeRankingPage(delta) {
  if (activeTab.value === 'red') handleRedListPageChange(redListPage.value + delta)
  else blackListPage.value += delta
}
</script>

<style scoped>
.company-layout {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr) 260px;
  gap: 22px;
  align-items: start;
}
.company-filters {
  position: sticky;
  top: 86px;
  padding: 18px;
}
.company-filters .business-field {
  margin-top: 20px;
}
.company-filters select {
  font-size: 13px;
}
.company-filters .business-panel-head {
  margin-bottom: 0;
}
.company-filters .business-panel-head h2 {
  font-size: 14px;
}
.company-filters .business-panel-head button {
  font-size: 12px;
}
.filter-note {
  border-top: 1px solid var(--career-border);
  padding-top: 20px;
  margin-top: 24px;
}
.filter-note h3 {
  font-size: 13px;
  font-weight: 500;
}
.filter-note p {
  margin: 8px 0 15px;
  color: var(--career-muted);
  font-size: 12px;
  line-height: 1.9;
}
.filter-note a {
  font-size: 12px;
}
.company-results {
  min-width: 0;
}
.job-search {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #ccd7e5;
  border-radius: 6px;
  background: #fff;
  padding: 0 12px;
}
.job-search svg {
  width: 17px;
  height: 17px;
  color: #8190a3;
  flex: none;
}
.job-search input {
  width: 100%;
  min-height: 42px;
  border: 0;
  padding-inline: 0;
  background: transparent;
  outline-offset: 0;
}
.job-search button {
  flex: none;
  font-size: 12px;
}
.job-results-summary {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 0 12px;
  font-size: 12px;
  color: #7a8799;
}
.job-results-summary strong {
  color: #344054;
  font-weight: 600;
}
.job-results-list {
  display: grid;
  gap: 10px;
}
.job-result-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 122px;
  gap: 14px;
  padding: 19px;
  border: 1px solid var(--career-border);
  border-radius: 7px;
  background: #fff;
}
.job-result-row:hover {
  border-color: #b9c9dc;
}
.job-result-row h2 {
  font-size: 16px;
  font-weight: 600;
  color: #27374d;
}
.job-company {
  color: #667085;
  font-size: 13px;
  margin-top: 6px;
}
.job-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 12px;
}
.job-description {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  color: #667085;
  font-size: 13px;
  line-height: 1.8;
  margin-top: 12px;
}
.job-company-detail {
  color: #8a97a8;
  font-size: 12px;
  margin-top: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.job-result-side {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-direction: column;
  gap: 18px;
}
.job-result-side > strong {
  color: #344054;
  font-size: 14px;
  font-weight: 500;
  text-align: right;
  line-height: 1.7;
}
.job-result-side .career-button {
  min-height: 30px;
  padding: 6px 10px;
  font-size: 12px;
}
.company-context .business-panel {
  padding: 18px;
}
.company-context h2 {
  font-size: 14px;
}
.fair-row {
  padding: 14px 0;
  border-top: 1px solid #edf0f4;
}
.fair-row h3 {
  font-size: 13px;
  font-weight: 500;
}
.fair-row a {
  display: inline-block;
  margin-top: 7px;
  font-size: 12px;
  line-height: 1.7;
}
.fair-row p {
  font-size: 12px;
  margin: 7px 0;
}
.context-note {
  margin-top: 14px;
}
.company-preparation {
  padding: 3px 12px;
}
.company-preparation h2 {
  color: #475467;
  font-size: 15px;
  line-height: 1.7;
  margin: 10px 0;
}
.company-preparation p:not(.career-eyebrow) {
  color: #7a8799;
  font-size: 13px;
  line-height: 1.9;
}
.company-preparation a {
  display: inline-block;
  margin-top: 15px;
  font-size: 13px;
}
.ranking-panel {
  padding: 20px;
}
.ranking-table-wrap {
  overflow-x: auto;
  margin-top: 20px;
}
.ranking-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 12px;
}
.ranking-table th {
  font-size: 12px;
  font-weight: 500;
  color: #7a8799;
  padding: 10px 8px;
  background: #f5f7fa;
  white-space: nowrap;
}
.ranking-table td {
  padding: 14px 8px;
  color: #667085;
  border-bottom: 1px solid #edf0f4;
  vertical-align: top;
  line-height: 1.8;
}
.ranking-table td:first-child {
  min-width: 130px;
}
.ranking-table td:last-child {
  min-width: 150px;
}
.ranking-table td strong {
  display: block;
  color: #344054;
  font-size: 13px;
  font-weight: 500;
}
.ranking-table td span {
  display: block;
  margin-top: 5px;
}
.ranking-table td:nth-child(3) {
  min-width: 85px;
}
.safety-content > .business-muted {
  margin-top: 9px;
}
.safety-content > article {
  display: flex;
  gap: 14px;
  padding: 22px 0;
  border-bottom: 1px solid var(--career-border);
}
.safety-content article p {
  color: #667085;
  font-size: 13px;
  margin-top: 8px;
}
.safety-marker {
  width: 7px;
  height: 7px;
  margin-top: 8px;
  border: 1px solid #b0874a;
  border-radius: 50%;
  flex: none;
}
.safety-content .business-notice {
  margin-top: 20px;
}
.advice-search {
  display: flex;
  gap: 10px;
  margin-bottom: 22px;
}
.advice-search input {
  min-width: 0;
  flex: 1;
}
.advice-search select {
  font-size: 13px;
}
.advice-row {
  border-top: 1px solid var(--career-border);
  padding: 22px 0 4px;
  margin-top: 18px;
}
.advice-row header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}
.advice-row header p {
  color: #667085;
  font-size: 13px;
  margin-top: 4px;
}
.advice-source {
  font-size: 12px !important;
  color: #8a97a8;
  margin-top: 12px;
}
.advice-body {
  margin-top: 12px;
  color: #586577;
  white-space: pre-line;
}
.advice-notes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-top: 16px;
}
.advice-notes strong {
  color: #667085;
  font-size: 12px;
  font-weight: 500;
}
.advice-notes p {
  color: #7a8799;
  font-size: 12px;
}
@media (max-width: 1180px) {
  .company-layout {
    grid-template-columns: 180px minmax(0, 1fr) 230px;
    gap: 16px;
  }
  .job-result-row {
    grid-template-columns: minmax(0, 1fr) 100px;
    padding: 16px;
  }
}
@media (max-width: 980px) {
  .company-layout {
    grid-template-columns: 180px minmax(0, 1fr);
  }
  .company-context {
    grid-column: 1 / -1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .company-filters {
    position: static;
  }
}
@media (max-width: 760px) {
  .company-layout {
    grid-template-columns: 1fr;
  }
  .company-context {
    grid-template-columns: 1fr;
  }
  .company-filters {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .company-filters .business-panel-head {
    grid-column: 1 / -1;
  }
  .filter-note {
    display: none;
  }
  .job-result-row {
    grid-template-columns: minmax(0,1fr) 100px;
  }
  .job-results-summary > span:last-child {
    display: none;
  }
}
</style>
