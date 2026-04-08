document.addEventListener('DOMContentLoaded', function () {
    // 1. 初始化 ECharts
    const chartDom = document.getElementById('mainChart');
    const myChart = echarts.init(chartDom);

    // 2. 渲染图表函数 (多轴联动)
    async function fetchAndRenderChart() {
        try {
            // 调用 Flask 接口获取历史数据
            const response = await fetch('/api/health/history');
            const result = await response.json();

            // 更新顶部 KPI 卡片 (取最新的一条数据)
            if (result.times && result.times.length > 0) {
                const lastIndex = result.times.length - 1;
                document.getElementById('kpi-hr').innerHTML = `${result.heart_rates[lastIndex]} <span>bpm</span>`;
                document.getElementById('kpi-sleep').innerHTML = `${result.sleep_hours[lastIndex]} <span>h</span>`;
                document.getElementById('kpi-steps').innerHTML = `${result.steps[lastIndex]} <span>步</span>`;
            }

            // ECharts 配置：左轴心率(折线)，右轴步数(柱状)
            const option = {
                tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                legend: { data: ['心率 (bpm)', '步数'], top: 0 },
                grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                xAxis: [
                    { type: 'category', data: result.times, boundaryGap: true }
                ],
                // 定义双 Y 轴
                yAxis: [
                    {
                        type: 'value',
                        name: '心率',
                        min: 40, max: 150, // 设定心率合理区间
                        axisLabel: { formatter: '{value} bpm' }
                    },
                    {
                        type: 'value',
                        name: '步数',
                        position: 'right', // 放在右侧
                        axisLabel: { formatter: '{value} 步' },
                        splitLine: { show: false } // 隐藏右轴网格线避免杂乱
                    }
                ],
                series: [
                    {
                        name: '步数',
                        type: 'bar',
                        yAxisIndex: 1, // 绑定到右侧 Y 轴
                        data: result.steps,
                        itemStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: '#83bff6' },
                                { offset: 1, color: '#188df0' }
                            ]),
                            borderRadius: [4, 4, 0, 0]
                        }
                    },
                    {
                        name: '心率 (bpm)',
                        type: 'line',
                        smooth: true,
                        data: result.heart_rates,
                        itemStyle: { color: '#ef233c' },
                        lineStyle: { width: 3 },
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: 'rgba(239, 35, 60, 0.3)' },
                                { offset: 1, color: 'rgba(239, 35, 60, 0)' }
                            ])
                        }
                    }
                ]
            };
            myChart.setOption(option);
        } catch (error) {
            console.error("图表数据获取失败:", error);
            // 可以在此处渲染备用/模拟数据防止图表空白
        }
    }

    // 3. 处理表单提交 (触发 AI)
    const form = document.getElementById('healthForm');
    const analyzeBtn = document.getElementById('analyzeBtn');

    form.addEventListener('submit', async function (e) {
        e.preventDefault(); // 阻止页面刷新

        // 改变按钮状态
        const originalText = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> AI 正在全息运算中...';
        analyzeBtn.disabled = true;

        // 获取用户输入的数据
        const hr = document.getElementById('input-hr').value;
        const sleep = document.getElementById('input-sleep').value;
        const steps = document.getElementById('input-steps').value;

        try {
            // 第一步：先将数据发送给入库接口
            const uploadRes = await fetch('/api/sensor/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: 1,
                    heart_rate: parseInt(hr),
                    sleep_hours: parseFloat(sleep),
                    steps: parseInt(steps)
                })
            });

            if (uploadRes.ok) {
                // 第二步：触发 AI 诊断接口
                const analyzeRes = await fetch('/api/analyze/1', { method: 'POST' });
                const aiData = await analyzeRes.json();

                if (aiData.code === 200) {
                    const res = aiData.data;

                    // 显示结果区
                    document.getElementById('ai-result').classList.remove('hidden');

                    // 动态更新数字和文字
                    document.getElementById('res-score').innerText = res.health_score;
                    document.getElementById('res-level').innerText = res.risk_level;
                    document.getElementById('res-suggestion').innerText = res.suggestion;

                    // 根据风险等级改变圆圈颜色
                    const circle = document.querySelector('.score-circle');
                    if (res.risk_level === '高风险') {
                        circle.style.background = 'linear-gradient(135deg, #ff0844 0%, #ffb199 100%)';
                    } else if (res.risk_level === '中风险') {
                        circle.style.background = 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)';
                    } else {
                        circle.style.background = 'linear-gradient(135deg, #00b09b, #96c93d)';
                    }

                    // 刷新左侧图表
                    fetchAndRenderChart();
                }
            }
        } catch (error) {
            alert("通信失败，请确保 Flask 后端正在运行！");
        } finally {
            // 恢复按钮状态
            analyzeBtn.innerHTML = originalText;
            analyzeBtn.disabled = false;
        }
    });

    // 页面加载时执行一次渲染
    fetchAndRenderChart();

    // 监听窗口大小变化，让图表自适应缩放
    window.addEventListener('resize', () => myChart.resize());
});