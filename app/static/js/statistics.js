document.addEventListener('DOMContentLoaded', function () {
    const loadBtn = document.getElementById('loadStatisticsBtn');
    const resetBtn = document.getElementById('resetDateBtn');
    if (loadBtn) {
        loadBtn.addEventListener('click', loadStatistics);
    }
    if (resetBtn) {
        resetBtn.addEventListener('click', resetDate);
    }
    loadStatistics();
});

async function fetchJSON(url, options = {}) {
    const resp = await fetch(url, {
        headers: {'Content-Type': 'application/json'},
        ...options,
    });
    const data = await resp.json();
    if (!resp.ok) {
        throw new Error(data.error || '请求失败');
    }
    return data;
}

function resetDate() {
    document.getElementById('statisticsDate').value = '';
    loadStatistics();
}

async function loadStatistics() {
    const container = document.getElementById('statisticsContainer');
    const dateInput = document.getElementById('statisticsDate');
    const dateInfo = document.getElementById('dateInfo');
    const loadBtn = document.getElementById('loadStatisticsBtn');
    
    const atDate = dateInput.value || null;
    
    // 更新日期提示
    if (atDate) {
        dateInfo.textContent = `正在查询 ${atDate} 时间点的统计信息...`;
    } else {
        dateInfo.textContent = '正在查询最新状态的统计信息...';
    }
    
    loadBtn.disabled = true;
    loadBtn.classList.add('disabled');
    
    try {
        let url = '/api/statistics';
        if (atDate) {
            url += `?at_date=${atDate}`;
        }
        const result = await fetchJSON(url);
        const stats = result.data;
        container.innerHTML = renderStatistics(stats);
        
        // 更新日期提示
        if (stats.at_date) {
            dateInfo.innerHTML = `<span class="blue-text">✓ 已查询 ${stats.at_date} 时间点的统计信息</span>`;
        } else {
            dateInfo.innerHTML = '<span class="green-text">✓ 已查询最新状态的统计信息</span>';
        }
    } catch (err) {
        container.innerHTML = `<div class="red-text center-align">加载失败：${err.message}</div>`;
        dateInfo.innerHTML = `<span class="red-text">查询失败：${err.message}</span>`;
    } finally {
        loadBtn.disabled = false;
        loadBtn.classList.remove('disabled');
    }
}

function renderStatistics(stats) {
    return `
        <!-- 总体概况 -->
        <div class="card stat-card">
            <div class="card-content">
                <span class="card-title" style="font-size:20px;margin-bottom:20px;">总体概况</span>
                <div class="stat-grid">
                    <div class="stat-mini-card">
                        <div class="stat-mini-number">${stats.overview.total_count}</div>
                        <div class="stat-mini-label">人员总数</div>
                    </div>
                    <div class="stat-mini-card">
                        <div class="stat-mini-number">${stats.overview.employed_count}</div>
                        <div class="stat-mini-label">在职人数</div>
                    </div>
                    <div class="stat-mini-card">
                        <div class="stat-mini-number">${stats.overview.unemployed_count}</div>
                        <div class="stat-mini-label">离职人数</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 性别分布 -->
        <div class="card stat-card">
            <div class="card-content">
                <span class="card-title" style="font-size:20px;margin-bottom:20px;">性别分布</span>
                ${renderBarChart(stats.gender, stats.overview.total_count)}
            </div>
        </div>

        <!-- 年龄分布 -->
        <div class="card stat-card">
            <div class="card-content">
                <span class="card-title" style="font-size:20px;margin-bottom:20px;">年龄分布</span>
                ${renderBarChart(stats.age, stats.overview.total_count)}
            </div>
        </div>

        <!-- 组织架构统计 -->
        <div class="row">
            <div class="col s12 m6">
                <div class="card stat-card">
                    <div class="card-content">
                        <span class="card-title" style="font-size:20px;margin-bottom:20px;">按公司统计</span>
                        ${renderBarChart(stats.company, stats.overview.employed_count)}
                    </div>
                </div>
            </div>
            <div class="col s12 m6">
                <div class="card stat-card">
                    <div class="card-content">
                        <span class="card-title" style="font-size:20px;margin-bottom:20px;">按部门统计</span>
                        ${renderBarChart(stats.department, stats.overview.employed_count)}
                    </div>
                </div>
            </div>
        </div>

        <!-- 员工类别统计 -->
        <div class="card stat-card">
            <div class="card-content">
                <span class="card-title" style="font-size:20px;margin-bottom:20px;">按员工类别统计</span>
                ${renderBarChart(stats.employee_type, stats.overview.employed_count)}
            </div>
        </div>

        <!-- 薪资统计 -->
        <div class="row">
            <div class="col s12 m6">
                <div class="card stat-card">
                    <div class="card-content">
                        <span class="card-title" style="font-size:20px;margin-bottom:20px;">按薪资类型统计</span>
                        ${renderBarChart(stats.salary_type, stats.salary.count)}
                    </div>
                </div>
            </div>
            <div class="col s12 m6">
                <div class="card stat-card">
                    <div class="card-content">
                        <span class="card-title" style="font-size:20px;margin-bottom:20px;">薪资分布</span>
                        ${stats.salary.count > 0 ? `
                            <div style="margin-bottom:16px;">
                                <div class="stat-label">平均薪资</div>
                                <div class="stat-number">¥${stats.salary.average.toLocaleString()}</div>
                            </div>
                            ${renderBarChart(stats.salary.ranges, stats.salary.count)}
                        ` : '<p class="grey-text">暂无薪资数据</p>'}
                    </div>
                </div>
            </div>
        </div>

        <!-- 考核统计 -->
        <div class="card stat-card">
            <div class="card-content">
                <span class="card-title" style="font-size:20px;margin-bottom:20px;">按考核等级统计</span>
                ${Object.keys(stats.assessment).length > 0 ? renderBarChart(stats.assessment, Object.values(stats.assessment).reduce((a, b) => a + b, 0)) : '<p class="grey-text">暂无考核数据</p>'}
            </div>
        </div>

        <!-- 社保和公积金基数统计 -->
        <div class="row">
            <div class="col s12 m6">
                <div class="card stat-card">
                    <div class="card-content">
                        <span class="card-title" style="font-size:20px;margin-bottom:20px;">社保基数分布</span>
                        ${renderBarChart(stats.social_security_base, Object.values(stats.social_security_base).reduce((a, b) => a + b, 0))}
                    </div>
                </div>
            </div>
            <div class="col s12 m6">
                <div class="card stat-card">
                    <div class="card-content">
                        <span class="card-title" style="font-size:20px;margin-bottom:20px;">公积金基数分布</span>
                        ${renderBarChart(stats.housing_fund_base, Object.values(stats.housing_fund_base).reduce((a, b) => a + b, 0))}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderBarChart(data, total) {
    if (!data || Object.keys(data).length === 0) {
        return '<p class="grey-text">暂无数据</p>';
    }
    const maxValue = Math.max(...Object.values(data));
    return Object.entries(data)
        .sort((a, b) => b[1] - a[1])
        .map(([label, value]) => {
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
            const width = maxValue > 0 ? ((value / maxValue) * 100) : 0;
            return `
                <div class="stat-item">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:500;">${label}</span>
                        <span style="color:#1976d2;font-weight:500;">${value} 人 (${percentage}%)</span>
                    </div>
                    <div class="stat-bar">
                        <div class="stat-bar-fill" style="width:${width}%"></div>
                    </div>
                </div>
            `;
        })
        .join('');
}

