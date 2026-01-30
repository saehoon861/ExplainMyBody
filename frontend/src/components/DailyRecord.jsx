import React, { useState, useEffect } from 'react';
import { ClipboardCheck, Utensils, Dumbbell, Plus, Trash2, Save, Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import '../AppLight.css';

const DailyRecord = () => {
    const [userData, setUserData] = useState(null);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [foodItems, setFoodItems] = useState([]);
    const [exerciseItems, setExerciseItems] = useState([]);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            const parsedUser = JSON.parse(storedUser);
            setUserData(parsedUser);

            // Load records for the selected date
            if (parsedUser.daily_records && parsedUser.daily_records[selectedDate]) {
                const records = parsedUser.daily_records[selectedDate];
                setFoodItems(records.food || []);
                setExerciseItems(records.exercise || []);
            } else {
                setFoodItems([]);
                setExerciseItems([]);
            }
        }
    }, [selectedDate]);

    const addFoodItem = () => {
        setFoodItems([...foodItems, { name: '', calories: '' }]);
    };

    const addExerciseItem = () => {
        setExerciseItems([...exerciseItems, { name: '', duration: '', sets: '' }]);
    };

    const removeFoodItem = (index) => {
        setFoodItems(foodItems.filter((_, i) => i !== index));
    };

    const removeExerciseItem = (index) => {
        setExerciseItems(exerciseItems.filter((_, i) => i !== index));
    };

    const updateFoodItem = (index, field, value) => {
        const newItems = [...foodItems];
        newItems[index][field] = value;
        setFoodItems(newItems);
    };

    const updateExerciseItem = (index, field, value) => {
        const newItems = [...exerciseItems];
        newItems[index][field] = value;
        setExerciseItems(newItems);
    };

    const handleSave = async () => {
        if (!userData) return;
        setIsSaving(true);

        try {
            const response = await fetch(`http://localhost:5000/api/users/${userData.id}/records`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: selectedDate,
                    food: foodItems,
                    exercise: exerciseItems
                })
            });

            if (response.ok) {
                const updatedUser = await response.json();
                localStorage.setItem('user', JSON.stringify(updatedUser));
                setUserData(updatedUser);
                alert('기록이 저장되었습니다! 💪');
            } else {
                alert('저장에 실패했습니다. 잠시 후 다시 시도해주세요.');
            }
        } catch (error) {
            console.error('Error saving records:', error);
            alert('서버 연결 오류가 발생했습니다.');
        } finally {
            setIsSaving(false);
        }
    };

    const changeDate = (days) => {
        const date = new Date(selectedDate);
        date.setDate(date.getDate() + days);
        setSelectedDate(date.toISOString().split('T')[0]);
    };

    const totalCalories = foodItems.reduce((sum, item) => sum + (Number(item.calories) || 0), 0);

    return (
        <div className="main-content fade-in">
            <header className="dashboard-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <div className="icon-badge" style={{ background: '#e0f2fe', color: '#0ea5e9', padding: '8px', borderRadius: '12px' }}>
                        <ClipboardCheck size={24} />
                    </div>
                    <h1 style={{ margin: 0 }}>일일 기록</h1>
                </div>
                <p>그날의 건강한 습관을 꼼꼼하게 관리해보세요.</p>
            </header>

            {/* Date Selector */}
            <div className="dashboard-card" style={{ marginBottom: '24px', padding: '16px 24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <button onClick={() => changeDate(-1)} className="close-button"><ChevronLeft /></button>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '1.1rem' }}>
                        <Calendar size={20} color="#64748b" />
                        {selectedDate === new Date().toISOString().split('T')[0] ? '오늘' : selectedDate}
                    </div>
                    <button onClick={() => changeDate(1)} className="close-button"><ChevronRight /></button>
                </div>
            </div>

            {/* Food Section */}
            <div className="dashboard-card fade-in delay-1" style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ background: '#fef2f2', color: '#ef4444', padding: '8px', borderRadius: '12px' }}>
                            <Utensils size={20} />
                        </div>
                        <h3 style={{ margin: 0 }}>식단 기록</h3>
                    </div>
                    <div style={{ fontSize: '0.9rem', color: '#ef4444', fontWeight: 700 }}>
                        총 {totalCalories} kcal
                    </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {foodItems.map((item, index) => (
                        <div key={index} className="form-group-row" style={{ alignItems: 'flex-end' }}>
                            <div className="form-group" style={{ flex: 3 }}>
                                <label style={{ fontSize: '0.8rem' }}>음식 이름</label>
                                <input
                                    className="modal-input"
                                    placeholder="예: 닭가슴살 샐러드"
                                    value={item.name}
                                    onChange={(e) => updateFoodItem(index, 'name', e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ flex: 1.5 }}>
                                <label style={{ fontSize: '0.8rem' }}>칼로리</label>
                                <input
                                    className="modal-input"
                                    type="number"
                                    placeholder="kcal"
                                    value={item.calories}
                                    onChange={(e) => updateFoodItem(index, 'calories', e.target.value)}
                                />
                            </div>
                            <button
                                onClick={() => removeFoodItem(index)}
                                style={{ background: 'none', border: 'none', color: '#94a3b8', padding: '12px 0 12px 8px', cursor: 'pointer' }}
                            >
                                <Trash2 size={20} />
                            </button>
                        </div>
                    ))}
                    <button className="secondary-button" onClick={addFoodItem} style={{ borderStyle: 'dashed', background: '#f8fafc' }}>
                        <Plus size={18} /> 음식 추가
                    </button>
                </div>
            </div>

            {/* Exercise Section */}
            <div className="dashboard-card fade-in delay-2" style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                    <div style={{ background: '#f0fdf4', color: '#22c55e', padding: '8px', borderRadius: '12px' }}>
                        <Dumbbell size={20} />
                    </div>
                    <h3 style={{ margin: 0 }}>운동 기록</h3>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {exerciseItems.map((item, index) => (
                        <div key={index} className="form-group-row" style={{ alignItems: 'flex-end', gap: '8px' }}>
                            <div className="form-group" style={{ flex: 2.5 }}>
                                <label style={{ fontSize: '0.8rem' }}>운동 이름</label>
                                <input
                                    className="modal-input"
                                    placeholder="예: 스쿼트, 런닝"
                                    value={item.name}
                                    onChange={(e) => updateExerciseItem(index, 'name', e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label style={{ fontSize: '0.8rem' }}>시간/회</label>
                                <input
                                    className="modal-input"
                                    placeholder="예: 30분"
                                    value={item.duration}
                                    onChange={(e) => updateExerciseItem(index, 'duration', e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label style={{ fontSize: '0.8rem' }}>세트</label>
                                <input
                                    className="modal-input"
                                    placeholder="예: 3세트"
                                    value={item.sets}
                                    onChange={(e) => updateExerciseItem(index, 'sets', e.target.value)}
                                />
                            </div>
                            <button
                                onClick={() => removeExerciseItem(index)}
                                style={{ background: 'none', border: 'none', color: '#94a3b8', padding: '12px 0 12px 4px', cursor: 'pointer' }}
                            >
                                <Trash2 size={20} />
                            </button>
                        </div>
                    ))}
                    <button className="secondary-button" onClick={addExerciseItem} style={{ borderStyle: 'dashed', background: '#f8fafc' }}>
                        <Plus size={18} /> 운동 추가
                    </button>
                </div>
            </div>

            {/* Save Button */}
            <button
                className="primary-button fade-in delay-3"
                style={{ width: '100%', height: '56px', borderRadius: '18px', gap: '10px' }}
                onClick={handleSave}
                disabled={isSaving}
            >
                <Save size={20} /> {isSaving ? '저장 중...' : '오늘의 기록 저장하기'}
            </button>

            <div style={{ height: '40px' }}></div>
        </div>
    );
};

export default DailyRecord;
