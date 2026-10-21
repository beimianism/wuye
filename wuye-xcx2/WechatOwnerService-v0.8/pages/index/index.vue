<template>
	<view>
		<view class="margin-bottom-xs">
			<uni-notice-bar showIcon="true" scrollable="true" single="true" speed="30" text="欢迎访问HC智慧家园"></uni-notice-bar>
		</view>

		<scroll-view @scrolltolower="lower" class="scroll-restaurants-list" scroll-y="true" style="height:100%">
			<swiper class="categoryList padding-top-xs bg-white" indicator-dots="true" indicator-color="rgba(228,228,228,1)"
			 indicator-active-color="#FECA49">
				<block v-for="(item, index) in categoryList" :key="index">
					<swiper-item>
						<block v-for="(item, index2) in item" :key="index2">
							<view class="category-info" v-if="item.href != 'callProperty'">
								<navigator @tap="toPage(item.href)">
									<image :src="item.src" class="category-image"></image>
									<view class="category-text">{{item.name}}</view>
								</navigator>
							</view>
							<view class="category-info" v-if="item.href == 'callProperty'">
								<view @tap="callPropertyTel()">
									<image :src="item.src" class="category-image"></image>
									<view class="category-text">{{item.name}}</view>
								</view>
							</view>
						</block>
					</swiper-item>
				</block>
			</swiper>



		</scroll-view>
		<view class="cu-modal" :class="callPropertyModal==true?'show':''">
			<view class="cu-dialog">
				<view class="cu-bar bg-white justify-end">
					<view class="content">拨打电话</view>
					<view class="action" @tap="_cancleCall()">
						<text class="cuIcon-close text-red"></text>
					</view>
				</view>
				<view class="padding-xl">
					您确认拨打,{{property.communityName}}物业客服电话<br />{{property.sCommunityTel}}
				</view>
				<view class="cu-bar bg-white justify-end">
					<view class="action margin-0 flex-sub  solid-left" @tap="_cancleCall()">取消</view>
					<view class="action margin-0 flex-sub text-green solid-left" @tap="_doCall()">拨号</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import uniNoticeBar from '@/components/uni-notice-bar/uni-notice-bar.vue'
	import {getCategoryList} from '../../api/index/indexApi.js'
	import {getProperty} from '../../api/property/propertyApi.js'

	import {getCurOwner} from '../../api/owner/ownerApi.js'

	import {hasLogin} from '../../auth/Java110Auth.js'
	export default {
		data() {
			return {
				communityId: '',
				property: {},
				callPropertyModal: false,
				categoryList: {},
				selected: 0,
				mask1Hidden: true,
				mask2Hidden: true,
				animationData: "",
				location: "",
				characteristicSelected: [false, false, false, false, false, false, false],
				discountSelected: null,
				selectedNumb: 0,
				sortSelected: "综合排序"
			};
		},
		components: {
			uniNoticeBar
		},
		/**
		 * 生命周期函数--监听页面加载
		 */
		onLoad: function(options) {
			let _that = this;
			this.vc.onLoad(options);		
			//查询目录
			this.categoryList = getCategoryList();
		},

		/**
		 * 生命周期函数--监听页面初次渲染完成
		 */
		onReady: function() {},
		onShareAppMessage:function() {
			return {
				title: '首页',
				path: '/pages/index/index?wAppId='+this.vc.getWAppId(),
				success: function(res) {
					// 转发成功
				},
				fail: function(res) {
					// 转发失败
				}
			}
		},
		/**
		 * 生命周期函数--监听页面显示
		 */
		onShow: function() {
			let _that = this;
			_that.location = this.vc.getStorageSync('location');
			if (hasLogin()) {
				_that.judgeBindOwnerFun();
			}
			this._initIndexData();
		},

		methods: {
			_initIndexData: function() {
				let _that = this;
				//查询当前小区信息
				this.vc.getCurCommunity()
				.then(function(_communityInfo){
					_that.communityId = _communityInfo.communityId;
					//查询小区活动信息

				})
			},
			judgeBindOwnerFun: function() {
				//查询业主
				getCurOwner();
			},
			showModal: function(e) {
				this.vc.navigateTo({
					url: '../bindOwner/bindOwner'
				});
			},
			callPropertyTel: function() { //拨打电话
				let _that = this;
				if (!hasLogin()) {
					this.vc.navigateTo({
						url: '../showlogin/showlogin'
					});
					return;
				}
				uni.getStorage({
					key: 'ownerInfo',
					success: function (res) {
						console.log(res.data);
						_that.property = res.data;
						_that.callPropertyModal = true;
					}
				});
			},
			_doCall: function() {
				let _that = this;
				uni.makePhoneCall({
					// 手机号
					phoneNumber: _that.property.sCommunityTel,
					// 成功回调
					success: (res) => {
						console.log('调用成功!')
					},
					// 失败回调
					fail: (res) => {
						console.log('调用失败!')
					}
				});
			},
			_cancleCall: function() {
				this.callPropertyModal = false;
			},
			toPage: function(pageUrl) {
				this.vc.navigateTo({
					url: pageUrl
				});
			},
		}
	};
</script>
<style>
	@import "./index.css";

	.bock-icon {
		height: 34upx;
		width: 14upx;
		line-height: 100upx;
		background-color: #00AA00;
	}

	.margin-top-1 {
		margin-top: 2upx;
	}

	.tec-height {
		height: 120upx;
	}
</style>
