import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import Layout from '../components/Layout';
import './OcrInputPage.css';

const OcrInputPage = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [step, setStep] = useState(1); // 1: 이미지 업로드, 2: 데이터 확인/수정
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [extractedData, setExtractedData] = useState(null);
    const [nullFields, setNullFields] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImageFile(file);
            setImagePreview(URL.createObjectURL(file));
        }
    };

    const handleExtract = async () => {
        if (!imageFile) {
            setError('이미지를 선택해주세요.');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await healthService.extractInbodyFromImage(imageFile);
            console.log('OCR Response:', response);

            // 백엔드 응답 구조: { data: InBodyData, null_fields: {...}, message: "..." }
            setExtractedData(response.data);
            setNullFields(response.null_fields || {});
            setStep(2);
        } catch (err) {
            console.error('OCR Error:', err);
            setError(err.response?.data?.detail || 'OCR 처리 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleNestedDataChange = (section, field, value) => {
        setExtractedData({
            ...extractedData,
            [section]: {
                ...extractedData[section],
                [field]: value ? (isNaN(value) ? value : parseFloat(value)) : null,
            }
        });
    };

    const handleSave = async () => {
        setLoading(true);
        setError('');

        try {
            // 백엔드로 전체 중첩 구조 전송
            await healthService.validateAndSaveInbody(user.id, extractedData);
            alert('인바디 데이터가 성공적으로 저장되었습니다!');
            navigate('/health-records');
        } catch (err) {
            console.error('Save Error:', err);
            setError(err.response?.data?.detail || '저장 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const renderFormField = (section, field, label, unit = '') => {
        const value = extractedData?.[section]?.[field];
        const isNull = value === null || value === undefined;

        return (
            <div className={`form-group ${isNull ? 'null-field' : ''}`}>
                <label>
                    {label} {unit && `(${unit})`}
                    {isNull && <span className="null-badge">검증 필요</span>}
                </label>
                <input
                    type={typeof value === 'string' ? 'text' : 'number'}
                    step="0.1"
                    value={value ?? ''}
                    onChange={(e) => handleNestedDataChange(section, field, e.target.value)}
                    placeholder={isNull ? '값을 입력하세요' : ''}
                />
            </div>
        );
    };

    return (
        <Layout>
            <div className="ocr-page">
                <h1>인바디 사진 업로드</h1>
                <p className="subtitle">인바디 측정 결과를 사진으로 찍어 업로드하면 자동으로 데이터를 추출합니다</p>

                {step === 1 && (
                    <div className="upload-section">
                        <div className="upload-card">
                            <div className="image-upload-area">
                                {imagePreview ? (
                                    <img src={imagePreview} alt="Preview" className="image-preview" />
                                ) : (
                                    <div className="upload-placeholder">
                                        <span className="icon">📷</span>
                                        <p>인바디 결과지 사진을 선택하세요</p>
                                    </div>
                                )}
                            </div>

                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleImageChange}
                                className="file-input"
                                id="file-input"
                            />
                            <label htmlFor="file-input" className="file-label">
                                이미지 선택
                            </label>

                            {error && <div className="error-message">{error}</div>}

                            <button
                                onClick={handleExtract}
                                disabled={!imageFile || loading}
                                className="extract-btn"
                            >
                                {loading ? 'OCR 처리 중...' : '데이터 추출'}
                            </button>
                        </div>
                    </div>
                )}

                {step === 2 && extractedData && (
                    <div className="data-review-section">
                        <div className="review-card">
                            <h2>추출된 데이터 확인 및 수정</h2>
                            <p className="info-text">데이터를 확인하고 필요시 수정하세요</p>

                            {Object.keys(nullFields).length > 0 && (
                                <div className="null-warning">
                                    ⚠️ 일부 필드가 추출되지 않았습니다. 직접 입력해주세요.
                                </div>
                            )}

                            <div className="data-form">
                                {/* 기본정보 */}
                                <div className="section-header">기본정보</div>
                                <div className="form-row">
                                    {renderFormField('기본정보', '신장', '신장', 'cm')}
                                    {renderFormField('기본정보', '연령', '연령', '세')}
                                    {renderFormField('기본정보', '성별', '성별')}
                                </div>

                                {/* 체성분 */}
                                <div className="section-header">체성분</div>
                                <div className="form-row">
                                    {renderFormField('체성분', '체수분', '체수분', 'L')}
                                    {renderFormField('체성분', '단백질', '단백질', 'kg')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('체성분', '무기질', '무기질', 'kg')}
                                    {renderFormField('체성분', '체지방', '체지방', 'kg')}
                                </div>

                                {/* 체중관리 */}
                                <div className="section-header">체중관리</div>
                                <div className="form-row">
                                    {renderFormField('체중관리', '체중', '체중', 'kg')}
                                    {renderFormField('체중관리', '골격근량', '골격근량', 'kg')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('체중관리', '체지방량', '체지방량', 'kg')}
                                    {renderFormField('체중관리', '적정체중', '적정체중', 'kg')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('체중관리', '체중조절', '체중조절', 'kg')}
                                    {renderFormField('체중관리', '지방조절', '지방조절', 'kg')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('체중관리', '근육조절', '근육조절', 'kg')}
                                </div>

                                {/* 비만분석 */}
                                <div className="section-header">비만분석</div>
                                <div className="form-row">
                                    {renderFormField('비만분석', 'BMI', 'BMI')}
                                    {renderFormField('비만분석', '체지방률', '체지방률', '%')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('비만분석', '복부지방률', '복부지방률')}
                                    {renderFormField('비만분석', '내장지방레벨', '내장지방레벨')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('비만분석', '비만도', '비만도', '%')}
                                </div>

                                {/* 연구항목 */}
                                <div className="section-header">연구항목</div>
                                <div className="form-row">
                                    {renderFormField('연구항목', '제지방량', '제지방량', 'kg')}
                                    {renderFormField('연구항목', '기초대사량', '기초대사량', 'kcal')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('연구항목', '권장섭취열량', '권장섭취열량', 'kcal')}
                                </div>

                                {/* 부위별근육분석 */}
                                <div className="section-header">부위별 근육 분석</div>
                                <div className="form-row">
                                    {renderFormField('부위별근육분석', '왼쪽팔', '왼쪽팔')}
                                    {renderFormField('부위별근육분석', '오른쪽팔', '오른쪽팔')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('부위별근육분석', '복부', '복부')}
                                    {renderFormField('부위별근육분석', '왼쪽하체', '왼쪽하체')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('부위별근육분석', '오른쪽하체', '오른쪽하체')}
                                </div>

                                {/* 부위별체지방분석 */}
                                <div className="section-header">부위별 체지방 분석</div>
                                <div className="form-row">
                                    {renderFormField('부위별체지방분석', '왼쪽팔', '왼쪽팔')}
                                    {renderFormField('부위별체지방분석', '오른쪽팔', '오른쪽팔')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('부위별체지방분석', '복부', '복부')}
                                    {renderFormField('부위별체지방분석', '왼쪽하체', '왼쪽하체')}
                                </div>
                                <div className="form-row">
                                    {renderFormField('부위별체지방분석', '오른쪽하체', '오른쪽하체')}
                                </div>
                            </div>

                            {error && <div className="error-message">{error}</div>}

                            <div className="button-group">
                                <button onClick={() => setStep(1)} className="back-btn">
                                    뒤로 가기
                                </button>
                                <button onClick={handleSave} disabled={loading} className="save-btn">
                                    {loading ? '저장 중...' : '저장하기'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default OcrInputPage;
